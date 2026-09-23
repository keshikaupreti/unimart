'use client';
import * as Dialog from '@radix-ui/react-dialog';
import { X } from 'lucide-react';
import { motion } from 'motion/react';
export default function Modal({ title, description, open, onClose, children, wide = false }: { title: string; description?: string; open: boolean; onClose: () => void; children: React.ReactNode; wide?: boolean }) {
  return <Dialog.Root open={open} onOpenChange={value => { if (!value) onClose(); }}><Dialog.Portal><Dialog.Overlay className="modal-overlay"/><Dialog.Content className={`modal ${wide ? 'modal-wide' : ''}`} aria-describedby={description ? undefined : undefined}><motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .2 }}><div className="modal-heading"><div><Dialog.Title>{title}</Dialog.Title>{description && <Dialog.Description>{description}</Dialog.Description>}</div><Dialog.Close className="icon-button" aria-label="Close dialog"><X size={20}/></Dialog.Close></div>{children}</motion.div></Dialog.Content></Dialog.Portal></Dialog.Root>;
}
