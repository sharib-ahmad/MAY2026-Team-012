import { ImageOff, Expand } from 'lucide-react';

export default function DonationImages({ images, alt, thumbClass = 'w-full h-40 object-cover', onClick }) {
  const src = images && images.length > 0 ? images[0] : null;
  const count = images?.length || 0;
  const clickable = typeof onClick === 'function';

  if (!src) {
    return (
      <div className={`${thumbClass} bg-primary/5 flex items-center justify-center text-primary/40`}>
        <ImageOff size={28} strokeWidth={1.5} />
      </div>
    );
  }

  return (
    <div
      className={`relative group ${clickable ? 'cursor-pointer' : ''}`}
      onClick={clickable ? onClick : undefined}
      role={clickable ? 'button' : undefined}
      aria-label={clickable ? `View photo${count > 1 ? 's' : ''} of ${alt}` : undefined}
    >
      <img src={src} alt={alt} className={thumbClass} />
      {clickable && (
        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/25 transition flex items-center justify-center opacity-0 group-hover:opacity-100">
          <Expand className="text-white" size={20} />
        </div>
      )}
      {count > 1 && (
        <span className="absolute bottom-2 right-2 bg-black/60 text-white text-[10px] px-1.5 py-0.5 rounded-full">
          1/{count}
        </span>
      )}
    </div>
  );
}