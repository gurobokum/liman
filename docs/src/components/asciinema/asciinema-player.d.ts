declare module "asciinema-player" {
  export type Player = {
    dispose(): void;
  };

  export function create(
    src: string,
    element: HTMLElement,
    options?: {
      preload?: boolean;
      fit?: boolean;
      terminalFontSize?: string;
      theme?: string;
      poster?: string;
      speed?: number;
      cols?: number;
    },
  ): Player;
}
