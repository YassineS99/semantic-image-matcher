import { useState } from "react";
import "./App.css";

const API_BASE = "http://localhost:8000";

function App() {
  const [postText, setPostText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [selectedImageId, setSelectedImageId] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    setSelectedImageId(null);

    try {
      const postRes = await fetch(`${API_BASE}/posts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: postText }),
      });
      if (!postRes.ok) throw new Error("Failed to create post");
      const post = await postRes.json();

      const matchRes = await fetch(
        `${API_BASE}/posts/${post.post_id}/match?top_n=10`,
        { method: "POST" }
      );
      if (!matchRes.ok) throw new Error("Failed to run matching");
      const matchData = await matchRes.json();

      setResult(matchData);
      const firstSuggested = matchData.candidates.find((c) => c.decision === "suggested");
      setSelectedImageId(firstSuggested ? firstSuggested.image_id : null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="App" style={{ maxWidth: 700, margin: "40px auto", fontFamily: "sans-serif" }}>
      <h1>Image–Post Matcher</h1>
      <form onSubmit={handleSubmit}>
        <textarea
          value={postText}
          onChange={(e) => setPostText(e.target.value)}
          placeholder="Write a post about an animal..."
          rows={3}
          style={{ width: "100%", padding: 8, fontSize: 16 }}
        />
        <button type="submit" disabled={loading || !postText} style={{ marginTop: 8, padding: "8px 16px" }}>
          {loading ? "Matching..." : "Find Match"}
        </button>
      </form>

      {error && <p style={{ color: "red" }}>{error}</p>}

      {result && (
        <div style={{ marginTop: 24 }}>
          {result.best_match ? (
            <div>
              <h2>Best Match</h2>
              {(() => {
                const selected =
                  result.candidates.find((c) => c.image_id === selectedImageId) || result.best_match;
                return (
                  <>
                    <img
                      src={`${API_BASE}/images/${selected.filename}`}
                      alt={selected.subject}
                      style={{ width: 240, borderRadius: 8, display: "block", marginBottom: 8 }}
                    />
                    <p>
                      <strong>{selected.filename}</strong> ({selected.subject})
                      <br />
                      similarity: {selected.similarity.toFixed(4)}
                    </p>
                  </>
                );
              })()}
            </div>
          ) : (
            <p style={{ color: "#b45309" }}>No good match found for this post.</p>
          )}

          <h3>All Candidates</h3>
          <p style={{ fontSize: 13, color: "#666" }}>
            Click any suggested (green) image to make it the best match.
          </p>
          <ul style={{ padding: 0 }}>
            {result.candidates.map((c) => (
              <li
                key={c.image_id}
                onClick={() => c.decision === "suggested" && setSelectedImageId(c.image_id)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 12,
                  marginBottom: 10,
                  listStyle: "none",
                  cursor: c.decision === "suggested" ? "pointer" : "default",
                  border: c.image_id === selectedImageId ? "2px solid #16a34a" : "2px solid transparent",
                  borderRadius: 8,
                  padding: 6,
                }}
              >
                <img
                  src={`${API_BASE}/images/${c.filename}`}
                  alt={c.subject}
                  style={{
                    width: 80,
                    height: 80,
                    objectFit: "cover",
                    borderRadius: 4,
                    opacity: c.decision === "suggested" ? 1 : 0.4,
                  }}
                />
                <div style={{ color: c.decision === "suggested" ? "green" : "#999" }}>
                  <strong>{c.filename}</strong> ({c.subject}) — similarity {c.similarity.toFixed(4)} — {c.decision}
                  {c.reason && <div style={{ fontStyle: "italic", fontSize: 13 }}>{c.reason}</div>}
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default App;