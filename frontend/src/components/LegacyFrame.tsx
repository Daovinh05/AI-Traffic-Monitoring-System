import "./LegacyFrame.css";

type LegacyFrameProps = {
  title: string;
  path: string;
};

export function LegacyFrame({ title, path }: LegacyFrameProps) {
  return (
    <main className="legacy-frame-page">
      <iframe
        title={title}
        src={path}
        className="legacy-frame"
        allow="camera; microphone; autoplay; clipboard-read; clipboard-write"
      />
    </main>
  );
}
