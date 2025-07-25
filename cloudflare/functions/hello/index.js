export async function onRequest() {
  return new Response("Hello from index.js!", { status: 200 });
} 