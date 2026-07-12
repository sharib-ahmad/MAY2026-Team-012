import { createPortal } from 'react-dom';
import { useEffect, useState } from 'react';
import { X, ChevronLeft, ChevronRight, ImageOff } from 'lucide-react';

export default function ImageLightbox({ images = [], open, onClose, title }) {
  const [index, setIndex] = useState(0);
  const [prevOpen, setPrevOpen] = useState(open);

  if (open && !prevOpen) {
    setIndex(0);
    setPrevOpen(true);
  } else if (!open && prevOpen) {
    setPrevOpen(false);
  }

  useEffect(() => {
    if (!open) return;
    const onKey = (e) => {
      if (e.key === 'Escape') onClose();
      if (e.key === 'ArrowRight') setIndex((i) => (i + 1) % Math.max(images.length, 1));
      if (e.key === 'ArrowLeft') setIndex((i) => (i - 1 + images.length) % Math.max(images.length, 1));
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, images.length, onClose]);

  if (!open) return null;
  const hasImages = images.length > 0;

  return createPortal(
    <div
      className="fixed inset-0 z-[9999] bg-black/80 flex items-center justify-center p-4 fade-in"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
    >
      <button type="button" onClick={onClose} className="absolute top-4 right-4 text-white/70 hover:text-white">
        <X size={26} />
      </button>

      {title && <div className="absolute top-4 left-4 text-white/80 text-sm font-medium">{title}</div>}

      <div className="max-w-3xl w-full max-h-[85vh] flex items-center justify-center" onClick={(e) => e.stopPropagation()}>
        {hasImages ? (
          <img src={images[index]} alt={title || 'Photo'} className="max-h-[75vh] max-w-full object-contain rounded-lg" />
        ) : (
          <div className="w-full h-64 flex flex-col items-center justify-center text-white/50 bg-white/5 rounded-lg">
            <ImageOff size={36} strokeWidth={1.5} />
            <p className="text-sm mt-2">No photos attached</p>
          </div>
        )}
      </div>

      {images.length > 1 && (
        <>
          <button
            type="button"
            onClick={(e) => { e.stopPropagation(); setIndex((i) => (i - 1 + images.length) % images.length); }}
            className="absolute left-4 top-1/2 -translate-y-1/2 text-white/70 hover:text-white bg-white/10 rounded-full p-2"
          >
            <ChevronLeft size={22} />
          </button>
          <button
            type="button"
            onClick={(e) => { e.stopPropagation(); setIndex((i) => (i + 1) % images.length); }}
            className="absolute right-4 top-1/2 -translate-y-1/2 text-white/70 hover:text-white bg-white/10 rounded-full p-2"
          >
            <ChevronRight size={22} />
          </button>
          <div className="absolute bottom-5 left-1/2 -translate-x-1/2 flex gap-1.5">
            {images.map((_, i) => (
              <span key={i} className={`w-1.5 h-1.5 rounded-full ${i === index ? 'bg-white' : 'bg-white/30'}`} />
            ))}
          </div>
        </>
      )}
    </div>,
    document.body
  );
}