import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../api.js";

const CONDITIONS = [
  ["new", "New"],
  ["like_new", "Like new"],
  ["good", "Good"],
  ["fair", "Fair"],
  ["poor", "Poor"],
];

export default function ItemDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [item, setItem] = useState(null);
  const [form, setForm] = useState(null);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(null); // which action is in flight
  const [nextPhotoIndex, setNextPhotoIndex] = useState(0);
  const photoInputRef = useRef(null);

  const load = () =>
    api
      .getItem(id)
      .then((i) => {
        setItem(i);
        setForm({
          title: i.title,
          description: i.description,
          category: i.category,
          condition: i.condition,
          dimensions: i.dimensions,
          price_final: i.price_final ?? "",
          notes: i.notes,
        });
      })
      .catch((e) => setError(e.message));

  useEffect(() => {
    load();
  }, [id]);

  if (!item || !form) {
    return error ? <div className="banner error">{error}</div> : <p>Loading...</p>;
  }

  const run = async (action, fn) => {
    setBusy(action);
    setError(null);
    try {
      const updated = await fn();
      setItem(updated);
      return updated;
    } catch (e) {
      setError(e.message);
      throw e;
    } finally {
      setBusy(null);
    }
  };

  const saveEdits = () =>
    run("save", () =>
      api.updateItem(id, {
        title: form.title,
        description: form.description,
        category: form.category,
        condition: form.condition,
        dimensions: form.dimensions,
        price_final: form.price_final === "" ? null : Number(form.price_final),
        notes: form.notes,
      })
    );

  const addPhotos = (fileList) => {
    const files = Array.from(fileList);
    if (!files.length) return;
    run("photos", () => api.addPhotos(id, files));
  };

  const deleteItem = async () => {
    if (!confirm("Delete this item and its photos?")) return;
    await api.deleteItem(id);
    navigate("/");
  };

  const runSearch = () =>
    run("analyze", () => api.analyzeItem(id, 0)).then(() => setNextPhotoIndex(1));

  const tryAnotherPhoto = () =>
    run("analyze", () => api.analyzeItem(id, nextPhotoIndex)).then(() =>
      setNextPhotoIndex((n) => n + 1)
    );

  const pickComp = (compId) => run("match", () => api.selectMatch(id, { comp_id: compId }));
  const skipToManual = () => run("match", () => api.selectMatch(id, { skip: true }));
  const changeMatch = () => run("match", () => api.selectMatch(id, { reset: true }));

  const generateListing = () =>
    run("generate", async () => {
      await api.updateItem(id, {
        title: form.title,
        condition: form.condition,
        dimensions: form.dimensions,
        notes: form.notes,
      });
      return api.generateListing(id);
    }).then((updated) => {
      setForm((f) => ({
        ...f,
        title: updated.title,
        description: updated.description,
        category: updated.category,
        price_final: updated.price_final ?? "",
      }));
    });

  const hasMorePhotosToTry = nextPhotoIndex < item.photos.length;

  return (
    <div>
      {error && <div className="banner error">{error}</div>}

      <div className="photo-strip">
        {item.photos.map((p) => (
          <img key={p.id} src={p.url} alt="" />
        ))}
        <button
          type="button"
          className="secondary"
          onClick={() => photoInputRef.current?.click()}
        >
          + Add photos
        </button>
        <input
          ref={photoInputRef}
          type="file"
          accept="image/*"
          multiple
          hidden
          onChange={(e) => addPhotos(e.target.files)}
        />
      </div>

      <span className={`badge ${item.status}`}>{item.status}</span>

      <div className="card" style={{ marginTop: 16 }}>
        <h3 style={{ marginTop: 0 }}>1. Find the matching product</h3>
        <p className="help-text">
          Reverse image search (SerpApi / Google Lens) on your photos. Requires
          SERPAPI_API_KEY and PUBLIC_BASE_URL configured on the backend — see the
          README.
        </p>

        {item.match_status === "unmatched" && item.comps.length === 0 && (
          <button className="secondary" onClick={runSearch} disabled={busy === "analyze"}>
            {busy === "analyze" ? "Searching..." : "Run price search"}
          </button>
        )}

        {item.match_status === "unmatched" && item.comps.length > 0 && (
          <>
            <div className="help-text" style={{ marginTop: 4 }}>
              Which of these is actually your item?
            </div>
            <ul className="comp-list">
              {item.comps.map((c) => (
                <li key={c.id}>
                  <a href={c.source_link} target="_blank" rel="noreferrer">
                    {c.source_title}
                  </a>
                  <span>{c.price != null ? `$${c.price}` : "-"}</span>
                  <button
                    className="secondary"
                    onClick={() => pickComp(c.id)}
                    disabled={busy === "match"}
                    style={{ marginLeft: 8 }}
                  >
                    Use this
                  </button>
                </li>
              ))}
            </ul>
            <div className="btn-row">
              <button
                className="secondary"
                onClick={tryAnotherPhoto}
                disabled={busy === "analyze" || !hasMorePhotosToTry}
                title={!hasMorePhotosToTry ? "No more photos to try" : ""}
              >
                None of these match — try another photo
              </button>
              <button className="secondary" onClick={skipToManual} disabled={busy === "match"}>
                Not in search options — I'll enter it manually
              </button>
            </div>
          </>
        )}

        {item.match_status === "matched" && (
          <div className="banner info">
            Matched to:{" "}
            <strong>
              {item.comps.find((c) => c.id === item.selected_comp_id)?.source_title ??
                "(selected product)"}
            </strong>
            <div className="btn-row">
              <button className="secondary" onClick={changeMatch} disabled={busy === "match"}>
                Change match
              </button>
            </div>
          </div>
        )}

        {item.match_status === "manual" && (
          <div className="banner info">
            Entering this item manually — using the Title field below as the reference.
            <div className="btn-row">
              <button className="secondary" onClick={changeMatch} disabled={busy === "match"}>
                Search instead
              </button>
            </div>
          </div>
        )}
      </div>

      <div className="card" style={{ marginTop: 16 }}>
        <h3 style={{ marginTop: 0 }}>2. Condition &amp; dimensions</h3>
        <div className="form-row">
          <label htmlFor="item_condition">Condition</label>
          <select
            id="item_condition"
            value={form.condition}
            onChange={(e) => setForm({ ...form, condition: e.target.value })}
          >
            {CONDITIONS.map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </div>
        <div className="form-row">
          <label htmlFor="item_dimensions">
            Dimensions <span className="help-text">(optional — only if not on the matched product page)</span>
          </label>
          <input
            id="item_dimensions"
            placeholder='e.g. 30in W x 32in H x 28in D'
            value={form.dimensions}
            onChange={(e) => setForm({ ...form, dimensions: e.target.value })}
          />
        </div>
        <div className="form-row">
          <label htmlFor="item_notes">Private notes (not shown in listing)</label>
          <textarea
            id="item_notes"
            value={form.notes}
            onChange={(e) => setForm({ ...form, notes: e.target.value })}
          />
        </div>
        <div className="btn-row">
          <button
            onClick={generateListing}
            disabled={item.match_status === "unmatched" || busy === "generate"}
          >
            {busy === "generate" ? "Writing listing..." : "3. Generate listing & price"}
          </button>
          {item.match_status === "unmatched" && (
            <span className="help-text">Pick a match (or go manual) above first.</span>
          )}
        </div>
      </div>

      <div className="card" style={{ marginTop: 16 }}>
        <h3 style={{ marginTop: 0 }}>4. Review &amp; edit</h3>
        <div className="form-row">
          <label htmlFor="item_title">Title</label>
          <input
            id="item_title"
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
          />
        </div>
        <div className="form-row">
          <label htmlFor="item_category">Category</label>
          <input
            id="item_category"
            value={form.category}
            onChange={(e) => setForm({ ...form, category: e.target.value })}
          />
        </div>
        <div className="form-row">
          <label htmlFor="item_description">Description</label>
          <textarea
            id="item_description"
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
          />
        </div>
        <div className="form-row">
          <label htmlFor="item_price">
            Final asking price{" "}
            {item.price_suggested != null && (
              <span className="help-text">(AI suggested: ${item.price_suggested})</span>
            )}
          </label>
          <input
            id="item_price"
            type="number"
            step="0.01"
            value={form.price_final}
            onChange={(e) => setForm({ ...form, price_final: e.target.value })}
          />
          {item.ai_price_reasoning && (
            <div className="help-text">AI reasoning: {item.ai_price_reasoning}</div>
          )}
        </div>
        <div className="btn-row">
          <button onClick={saveEdits} disabled={busy === "save"}>
            {busy === "save" ? "Saving..." : "Save changes"}
          </button>
          <button className="danger" onClick={deleteItem}>
            Delete item
          </button>
        </div>
      </div>

      <div className="card" style={{ marginTop: 16 }}>
        <h3 style={{ marginTop: 0 }}>Post to Facebook Marketplace</h3>
        <div className="banner warn">
          This opens a real, visible browser window on this machine and pre-fills the
          listing form for you (title, price, description, photos). It never clicks
          Publish — you always review the listing and publish it yourself. Note:
          automating interactions with Facebook is against its Terms of Service and
          carries some risk to your account even with a human doing the final click.
        </div>
        <div className="btn-row">
          <button
            onClick={() => run("publish", () => api.publishAssist(id))}
            disabled={item.status !== "approved" || busy === "publish"}
          >
            {busy === "publish" ? "Opening browser..." : "Open pre-filled listing in browser"}
          </button>
          {item.status !== "approved" && (
            <span className="help-text">Set a final price and approve the item first.</span>
          )}
          {item.status === "draft" || item.status === "analyzed" ? (
            <button
              className="secondary"
              onClick={() => run("approve", () => api.approveItem(id))}
              disabled={form.price_final === "" || busy === "approve"}
            >
              {busy === "approve" ? "Approving..." : "Approve item"}
            </button>
          ) : null}
          {(item.status === "publish_started" || item.status === "approved") && (
            <button
              className="secondary"
              onClick={() => run("mark", () => api.markPublished(id))}
              disabled={busy === "mark"}
            >
              {busy === "mark" ? "Saving..." : "I published it - mark as posted"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
