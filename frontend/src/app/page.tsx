"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";
import { signIn, signUp, supabase } from "@/lib/api";
import { Button, CategoryTab, Notice, StatusMark } from "@/components/ui";

const EXAMPLE = [
  { asked: "10x 6205 sealed bearings", tab: "bearing", pn: "6205-2RS1", brand: "Norvik", spec: "25 × 52 × 15 mm · sealed", status: "matched" },
  { asked: "4 belts A42", tab: "belt", pn: "A42", brand: "Norvik", spec: "Section A · 42 in", status: "matched" },
  { asked: "sealed bearing for 25mm shaft", tab: "bearing", pn: "6005 · 6205 · 6305", brand: "3 options", spec: "outer diameter missing", status: "needs_choice" },
] as const;

export default function SignInPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"signin" | "signup">("signup");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => data.session && router.replace("/buyer"));
  }, [router]);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await (mode === "signup" ? signUp(email, password) : signIn(email, password));
      router.replace(mode === "signup" ? "/buyer/new" : "/buyer");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong. Try again.");
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-dvh flex-col">
      <header className="bg-catalog text-white">
        <div className="mx-auto flex h-14 max-w-[1240px] items-center px-5 text-[1.0625rem] font-bold tracking-tight">
          Parts<span className="font-normal">Bridge</span>
        </div>
      </header>

      <main className="mx-auto grid w-full max-w-[1240px] flex-1 items-start gap-12 px-5 py-12 lg:grid-cols-[1fr_380px] lg:py-20">
        <section className="max-w-[640px]">
          <h1 className="text-[2rem] leading-[2.375rem] font-bold tracking-tight text-balance">
            Paste a parts request. Get a catalog-matched list and quotes back.
          </h1>
          <p className="mt-4 max-w-[60ch] text-[1rem] leading-6 text-ink-2">
            AI reads the request, matches every line to the catalog, and asks you when it isn’t sure. Sellers answer with
            quotes drafted by AI and checked by a person. Try both sides: one account has a buyer and a seller workspace.
          </p>

          <figure className="mt-10" aria-label="Example of a matched request">
            <figcaption className="mb-2 text-label font-semibold uppercase tracking-wider text-ink-2">
              “Hi, need 10x 6205 sealed bearings, 4 belts A42, and a sealed bearing for a 25mm shaft”
            </figcaption>
            <table className="w-full border-y border-ink text-left">
              <thead className="bg-band text-label font-semibold uppercase tracking-wider text-ink-2">
                <tr>
                  <th className="w-10 p-0" />
                  <th className="px-3 py-2">You asked for</th>
                  <th className="px-3 py-2">Catalog match</th>
                  <th className="px-3 py-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {EXAMPLE.map((row) => (
                  <tr key={row.asked} className="border-t border-rule">
                    <td className="p-0 align-middle"><CategoryTab category={row.tab} /></td>
                    <td className="px-3 py-2.5 text-ink-2">{row.asked}</td>
                    <td className="px-3 py-2.5">
                      <div className="flex items-baseline gap-2">
                        <span className="condensed text-figure font-bold">{row.pn}</span>
                        <span className="text-label font-semibold uppercase tracking-wider text-ink-2">{row.brand}</span>
                      </div>
                      <div className="text-ink-2">{row.spec}</div>
                    </td>
                    <td className="px-3 py-2.5"><StatusMark status={row.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </figure>
        </section>

        <section className="border-t-[3px] border-catalog bg-band-2 p-6">
          <div role="tablist" aria-label="Account" className="mb-6 flex gap-5 border-b border-rule">
            {(["signup", "signin"] as const).map((m) => (
              <button
                key={m}
                role="tab"
                aria-selected={mode === m}
                onClick={() => { setMode(m); setError(null); }}
                className={`-mb-px border-b-2 pb-2 font-semibold ${mode === m ? "border-catalog text-ink" : "border-transparent text-ink-2 hover:text-ink"}`}
              >
                {m === "signup" ? "Create account" : "Sign in"}
              </button>
            ))}
          </div>

          <form onSubmit={submit} className="space-y-4">
            <label className="block">
              <span className="mb-1 block font-semibold">Email</span>
              <input
                type="email" required autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)}
                className="h-10 w-full rounded-[3px] border border-rule-strong bg-paper px-3 hover:border-ink-2 focus:border-catalog focus:outline-none"
              />
            </label>
            <label className="block">
              <span className="mb-1 block font-semibold">Password</span>
              <input
                type="password" required minLength={8} autoComplete={mode === "signup" ? "new-password" : "current-password"}
                value={password} onChange={(e) => setPassword(e.target.value)}
                className="h-10 w-full rounded-[3px] border border-rule-strong bg-paper px-3 hover:border-ink-2 focus:border-catalog focus:outline-none"
              />
              {mode === "signup" && <span className="mt-1 block text-label text-ink-2">At least 8 characters.</span>}
            </label>
            {error && <Notice>{error}</Notice>}
            <Button type="submit" variant="primary" busy={busy} className="h-10 w-full">
              {mode === "signup" ? "Create account and start" : "Sign in"}
            </Button>
          </form>
          {mode === "signup" && (
            <p className="mt-4 text-label leading-5 text-ink-2">
              Your account comes with a seller shop and three sample requests from buyers, so you can try both sides.
            </p>
          )}
        </section>
      </main>
    </div>
  );
}
