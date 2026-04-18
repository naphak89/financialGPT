import { Suspense } from "react";
import { TextbookReader } from "./TextbookReader";

export default function TextbookPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-[100dvh] items-center justify-center bg-background text-sm text-muted">
          Loading reader…
        </div>
      }
    >
      <TextbookReader />
    </Suspense>
  );
}
