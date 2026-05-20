const apiUrl = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export default function App() {
  return (
    <main style={{ fontFamily: "system-ui, sans-serif", padding: "2rem" }}>
      <h1>Cyber Threats</h1>
      <p>Frontend is running. API base URL: {apiUrl}</p>
    </main>
  );
}
