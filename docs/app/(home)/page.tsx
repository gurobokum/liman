import Link from "next/link";

export default function HomePage() {
  return (
    <main className="flex flex-1 flex-col justify-center text-center">
      <h1 className="mb-4 text-4xl font-bold">Liman</h1>
      <p className="text-fd-muted-foreground mb-4">
        Framework for buiding distributed and reliable AI Agents
      </p>
      <p className="text-fd-muted-foreground">
        You can open{" "}
        <Link
          href="/docs/poc"
          className="text-fd-foreground font-semibold underline"
        >
          PoC
        </Link>{" "}
        and see the documentation.
      </p>
    </main>
  );
}
