import Image from "next/image";

export function MemeIcon({ src }: { src: string }) {
  return (
    <span className="inline-block">
      <Image src={src} className="!m-0" height={14} width={14} alt="" />
    </span>
  );
}
