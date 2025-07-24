export async function POST(request: Request) {
  const body = await request.json();
  const { email } = body;

  if (!email) {
    return new Response("Missing email", { status: 400 });
  }

  const apiKey = process.env.MAILERLITE_API_KEY;
  if (!apiKey) {
    return new Response("API key not configured", { status: 500 });
  }

  try {
    await fetch("https://connect.mailerlite.com/api/subscribers", {
      method: "POST",
      body: JSON.stringify({ email }),
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiKey}`,
      },
    });
    return new Response("ok");
  } catch (e) {
    console.error("Error sending email to MailerLite", e);
    return new Response("Error processing email", { status: 500 });
  }
}
