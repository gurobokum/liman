"use client";
import { useEffect, useRef } from "react";
import { useTheme } from "next-themes";
import type { Player } from "asciinema-player";
import "./style.css";

export default function ASCIinema({ src }: { src: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const { theme } = useTheme();

  useEffect(() => {
    let player: Player | null = null;
    let cleaned = false;

    if (!ref.current) return;
    const loadPlayer = async () => {
      const ASCIinemaPlayer = await import("asciinema-player");
      if (cleaned) return;
      if (!ref.current) return;

      player = ASCIinemaPlayer.create(src, ref.current, {
        preload: true,
        fit: false,
        terminalFontSize: "small",
        //theme: "light",
        theme: theme === "light" ? "light" : "asciinema",
        poster: "data:text/plain,Click to check the demo.. ",
        speed: 2,
        cols: 131,
      });
    };

    loadPlayer();

    return () => {
      cleaned = true;
      if (player) {
        console.log("Disposing ASCIinema instance", ASCIinema);
        player.dispose();
      }
    };
  }, [theme, src]);

  return <div ref={ref} className="overflow-x-scroll"></div>;
}
