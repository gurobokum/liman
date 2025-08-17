export function Meme({ src, className }: { src: string; className?: string }) {
  return (
    <span className="inline-block">
      <img src={src} className={`!m-0 ${className}`} />
    </span>
  );
}
