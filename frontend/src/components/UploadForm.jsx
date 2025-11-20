import React, { useState } from "react";
import axios from "axios";

export default function UploadForm() {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);

  const API_BASE = "http://localhost:8000";

  const searchFaces = async () => {
    if (!file) {
      setStatus("Please select an image first.");
      return;
    }

    setStatus("");
    setLoading(true);
    setResults([]);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post(`${API_BASE}/search`, formData);
      const matches = response.data.matches;

      if (!matches || matches.length === 0) {
        setStatus("No similar faces found.");
      } else {
        setResults(matches);
        setStatus(
          `Found ${matches.length} match${matches.length > 1 ? "es" : ""}!`
        );
      }
    } catch (error) {
      console.error(error);
      setStatus("Error occurred while searching faces.");
    }

    setLoading(false);
  };

  const downloadImage = (b64, filename) => {
    const link = document.createElement("a");
    link.href = `data:image/jpeg;base64,${b64}`;
    link.download = filename;
    link.click();
  };

  return (
    <div className="upload-form">
      <h2 className="title">Search for Similar Faces</h2>

      {/* File picker & search button */}
      <div className="form-row">
        <input
          type="file"
          accept="image/*"
          className="file-input"
          aria-label="Upload image to search for matching faces"
          onChange={(e) => setFile(e.target.files[0])}
        />

        <button
          onClick={searchFaces}
          className="primary-btn"
          disabled={loading}
          aria-label="Search for similar faces"
        >
          {loading ? "Searching..." : "Search"}
        </button>
      </div>

      {/* Status text */}
      {status && (
        <p
          className="status-text"
          style={{
            color: status.includes("Error") || status.includes("failed")
              ? "#f44336"
              : "#222",
          }}
        >
          {status}
        </p>
      )}

      {/* Results */}
      <div className="result-grid">
        {results.map((match, index) => (
          <div key={index} className="result-card">
            <img
              src={`data:image/jpeg;base64,${match.image_base64}`}
              alt={`Matched face: ${match.filename}`}
            />

            <p style={{ color: "#2196f3", fontWeight: 600 }}>
              {match.filename}
            </p>

            <p className="muted">
              Similarity:{" "}
              <span style={{ color: "#4fc3f7" }}>
                {match.distance.toFixed(4)}
              </span>
            </p>

            <button
              onClick={() => downloadImage(match.image_base64, match.filename)}
              className="primary-btn"
              aria-label={`Download image ${match.filename}`}
              style={{ padding: "8px 16px", fontSize: "0.9em" }}
            >
              Download
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
