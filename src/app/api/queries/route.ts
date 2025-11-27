import { NextResponse } from "next/server";

export async function POST(req: Request) {
  const body = await req.json();
  const query = body.query || "";

  if (!query.trim()) {
    return new NextResponse("Invalid query", { status: 400 });
  }

  // FAKE QUERY ID
  const fakeReportId =
    "demo-" +
    Math.random().toString(36).substring(2, 10) +
    Date.now().toString().slice(-5);

  return NextResponse.json({
    queryId: fakeReportId,
    message: "Query saved. Report will be generated shortly.",
  });
}
