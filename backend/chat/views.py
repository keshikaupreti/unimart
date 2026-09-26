from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models import Q
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Conversation
from .serializers import ConversationSerializer, MessageSerializer


def conversation_group(conversation_id):
    return f"conversation_{conversation_id.hex}"


class ConversationViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return (
            Conversation.objects.filter(Q(buyer=user) | Q(seller=user))
            .select_related("listing", "buyer", "seller")
        )

    def perform_create(self, serializer):
        listing = serializer.validated_data["listing"]
        serializer.save(buyer=self.request.user, seller=listing.seller)

    @action(detail=True, methods=["post", "delete"])
    def archive(self, request, pk=None):
        conversation = self.get_object()
        field = "buyer_archived" if request.user.id == conversation.buyer_id else "seller_archived"
        setattr(conversation, field, request.method == "POST")
        conversation.save(update_fields=[field])
        return Response(self.get_serializer(conversation).data)

    @action(detail=True, methods=["get", "post"])
    def messages(self, request, pk=None):
        conversation = self.get_object()
        if request.method == "GET":
            queryset = conversation.messages.select_related("sender")
            page = self.paginate_queryset(queryset)
            if page is not None:
                data = MessageSerializer(page, many=True).data
                return self.get_paginated_response(data)
            return Response(MessageSerializer(queryset, many=True).data)

        serializer = MessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.save(
            conversation=conversation, sender=request.user,
        )
        conversation.save(update_fields=["updated_at"])
        data = MessageSerializer(message).data
        async_to_sync(get_channel_layer().group_send)(
            conversation_group(conversation.id),
            {"type": "chat.message", "message": data},
        )
        return Response(data, status=status.HTTP_201_CREATED)
