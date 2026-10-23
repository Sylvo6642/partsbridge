"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { LogOut } from "lucide-react";
import { api, supabase } from "@/lib/api";
import type { Me } from "@/lib/types";

const NAV = {
  buyer: [
    { href: "/buyer", label: "My requests" },
    { href: "/buyer/new", label: "New request" },
  ],
  seller: [{ href: "/seller", label: "Inbox" }],
};

const MeContext = createContext<Me | null>(null);

/** The login gate: no session (or an expired one) sends the visitor to the sign-in page. */
export function MeProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [me, setMe] = useState<Me | null>(null);

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      if (!data.session) router.replace("/");
      else api<Me>("/me").then(setMe).catch(() => router.replace("/"));
    });
  }, [router]);

  return <MeContext.Provider value={me}>{children}</MeContext.Provider>;
}

export function Wordmark({ href = "/buyer" }: { href?: string }) {
  return (
    <Link href={href} className="text-[1.0625rem] font-bold tracking-tight">
      Parts<span className="font-normal">Bridge</span>
    </Link>
  );
}

/** The catalog-blue top bar: role navigation, the Buyer/Seller switch and the account. */
export function ShellHeader() {
  const pathname = usePathname();
  const router = useRouter();
  const me = useContext(MeContext);
  const role = pathname.startsWith("/seller") ? "seller" : "buyer";

  async function signOut() {
    await supabase.auth.signOut();
    router.replace("/");
  }

  return (
    <header className="bg-catalog text-white">
      <div className="mx-auto flex h-14 max-w-[1240px] items-center gap-8 px-5">
        <Wordmark href={`/${role}`} />
        <nav aria-label={`${role} navigation`} className="flex h-full items-stretch gap-1">
          {NAV[role].map((item) => {
            const active = item.href === `/${role}` ? pathname === item.href || pathname.startsWith(`/${role}/requests`) : pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={active ? "page" : undefined}
                className={`flex items-center border-b-[3px] px-2.5 pt-[3px] font-semibold transition-colors ${
                  active ? "border-white text-white" : "border-transparent text-catalog-ink hover:text-white"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="ml-auto flex items-center gap-4">
          <div role="group" aria-label="Switch role" className="flex rounded-[3px] bg-catalog-deep p-0.5">
            {(["buyer", "seller"] as const).map((r) => (
              <Link
                key={r}
                href={`/${r}`}
                aria-pressed={role === r}
                className={`rounded-[2px] px-3 py-1 text-label font-bold uppercase tracking-wider transition-colors ${
                  role === r ? "bg-white text-catalog" : "text-catalog-ink hover:text-white"
                }`}
              >
                {r}
              </Link>
            ))}
          </div>
          {me && (
            <div className="hidden text-right leading-tight md:block">
              <div className="text-label font-semibold">{me.email}</div>
              <div className="text-label text-catalog-ink">{role === "seller" ? me.shop.name : "Buyer workspace"}</div>
            </div>
          )}
          <button onClick={signOut} className="rounded-[3px] p-1.5 text-catalog-ink hover:bg-catalog-deep hover:text-white" aria-label="Sign out" title="Sign out">
            <LogOut className="size-4" />
          </button>
        </div>
      </div>
    </header>
  );
}

export function useMe() {
  return useContext(MeContext);
}
