import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api.js";
import ItemCard from "../components/ItemCard.jsx";

export default function ItemsPage() {
  const [items, setItems] = useState([]);
  const [error, setError] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);
  const navigate = useNavigate();

  const refresh = () => api.listItems().then(setItems).catch((e) => setError(e.message));

  useEffect(() => {
    refresh();
  }, []);

  const handleFiles = async (fileList) => {
    const files = Array.from(fileList);
    if (!files.length) return;
    setUploading(true);
    setError(null);
    try {
      const item = await api.createItem("", files);
      navigate(`/items/${item.id}`);
    } catch (e) {
      setError(e.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      {error && <div className="banner error">{error}</div>}

      <div
        className={`dropzone ${dragActive ? "active" : ""}`}
        onClick={() => fileInputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDragActive(true);
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragActive(false);
          handleFiles(e.dataTransfer.files);
        }}
      >
        {uploading
          ? "Uploading..."
          : "Drop photos here (one or more photos of ONE item), or click to choose files"}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          multiple
          hidden
          onChange={(e) => handleFiles(e.target.files)}
        />
      </div>

      <h2 className="section-title">Your items ({items.length})</h2>
      {items.length === 0 ? (
        <p className="help-text">No items yet — upload some photos above to get started.</p>
      ) : (
        <div className="grid">
          {items.map((item) => (
            <ItemCard key={item.id} item={item} />
          ))}
        </div>
      )}
    </div>
  );
}
