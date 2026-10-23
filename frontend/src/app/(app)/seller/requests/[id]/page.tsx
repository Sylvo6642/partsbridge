import { Suspense } from "react";
import { Loading } from "@/components/ui";
import { QuoteEditor } from "./quote-editor";

export default function SellerRequestPage() {
  return (
    <Suspense fallback={<Loading />}>
      <QuoteEditor />
    </Suspense>
  );
}
