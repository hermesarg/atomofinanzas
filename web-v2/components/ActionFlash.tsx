"use client";

export default function ActionFlash({
  kind,
  active
}: {
  kind: "income" | "expense" | "transfer";
  active: boolean;
}) {
  return (
    <div
      className={"action-flash " + kind + (active ? " active" : "")}
      aria-hidden="true"
    >
      <span />
      <i />
      <b />
    </div>
  );
}
