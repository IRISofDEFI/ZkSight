export async function submitQuery(text: string) {
  const res = await fetch("/api/queries", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query: text }),
  });

  if (!res.ok) {
    throw new Error("Failed to submit query");
  }

  return res.json();
}
