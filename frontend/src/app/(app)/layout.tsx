import { Suspense } from "react";
import { MeProvider, ShellHeader } from "@/components/app-shell";

/** The header reads the URL (role, active tab), so it streams in after this static blue bar. */
function HeaderFallback() {
  return (
    <header className="bg-catalog text-white">
      <div className="mx-auto flex h-14 max-w-[1240px] items-center px-5 text-[1.0625rem] font-bold tracking-tight">
        Parts<span className="font-normal">Bridge</span>
      </div>
    </header>
  );
}

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <MeProvider>
      <div className="flex min-h-dvh flex-col">
        <Suspense fallback={<HeaderFallback />}>
          <ShellHeader />
        </Suspense>
        <main className="mx-auto w-full max-w-[1240px] flex-1 px-5 pt-8 pb-24">{children}</main>
      </div>
    </MeProvider>
  );
}
