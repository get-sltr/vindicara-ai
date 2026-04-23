// Type shim for asciinema-player v3.x, which ships as a Vite-friendly ESM
// bundle without first-party .d.ts declarations as of this version.
//
// Reference: https://docs.asciinema.org/manual/player/ (API signature)

declare module 'asciinema-player' {
  export interface CreateOptions {
    autoPlay?: boolean;
    loop?: boolean | number;
    speed?: number;
    idleTimeLimit?: number;
    theme?: string;
    poster?: string;
    fit?: 'width' | 'height' | 'both' | 'none' | false;
    terminalFontFamily?: string;
    terminalFontSize?: string;
    terminalLineHeight?: number;
    controls?: boolean | 'auto';
    startAt?: number | string;
    cols?: number;
    rows?: number;
    markers?: Array<[number, string]>;
    pauseOnMarkers?: boolean;
    logger?: Console;
  }

  export interface Player {
    play(): Promise<void>;
    pause(): Promise<void>;
    seek(location: number | string): Promise<void>;
    getCurrentTime(): number;
    getDuration(): number | null;
    dispose(): void;
  }

  export function create(
    src: string | { url: string } | { data: unknown },
    element: HTMLElement,
    opts?: CreateOptions,
  ): Player;
}

declare module 'asciinema-player/dist/bundle/asciinema-player.css';
