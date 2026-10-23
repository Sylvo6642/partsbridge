import { Suspense } from "react";
import { Loading } from "@/components/ui";
import { RequestView } from "./request-view";

export default function RequestPage() {
  return (
    <Suspense fallback={<Loading />}>
      <RequestView />
    </Suspense>
  );
}
