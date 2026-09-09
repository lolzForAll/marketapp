import { useEffect, useState } from "react";
import { api } from "../api.js";

const empty = {
  full_name: "",
  email: "",
  phone: "",
  address: "",
  city: "",
  neighborhood: "",
  preferred_contact_method: "Facebook Messenger",
  pickup_notes: "",
};

export default function SellerProfilePage() {
  const [form, setForm] = useState(empty);
  const [saving, setSaving] = useState(false);
  const [savedAt, setSavedAt] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api
      .getSellerProfile()
      .then((p) => setForm({ ...empty, ...p }))
      .catch((e) => setError(e.message));
  }, []);

  const set = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  const save = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const updated = await api.updateSellerProfile(form);
      setForm({ ...empty, ...updated });
      setSavedAt(Date.now());
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="card" style={{ maxWidth: 560 }}>
      <h2>Your seller details</h2>
      <p className="help-text">
        Used to pre-fill listings and generate pickup instructions. Your full
        address is kept for your own reference only (e.g. arranging pickups) —
        listings only ever use your city/neighborhood, never your exact
        address.
      </p>
      {error && <div className="banner error">{error}</div>}
      <form onSubmit={save}>
        <div className="form-row">
          <label htmlFor="full_name">Full name</label>
          <input id="full_name" value={form.full_name} onChange={set("full_name")} />
        </div>
        <div className="form-row">
          <label htmlFor="email">Contact email</label>
          <input id="email" type="email" value={form.email} onChange={set("email")} />
        </div>
        <div className="form-row">
          <label htmlFor="phone">Contact phone</label>
          <input id="phone" value={form.phone} onChange={set("phone")} />
        </div>
        <div className="form-row">
          <label htmlFor="preferred_contact_method">Preferred contact method (shown in listings)</label>
          <select
            id="preferred_contact_method"
            value={form.preferred_contact_method}
            onChange={set("preferred_contact_method")}
          >
            <option>Facebook Messenger</option>
            <option>Phone / text</option>
            <option>Email</option>
          </select>
        </div>
        <div className="form-row">
          <label htmlFor="city">City</label>
          <input id="city" value={form.city} onChange={set("city")} />
        </div>
        <div className="form-row">
          <label htmlFor="neighborhood">Neighborhood / general area (used in listings)</label>
          <input id="neighborhood" value={form.neighborhood} onChange={set("neighborhood")} />
        </div>
        <div className="form-row">
          <label htmlFor="address">Full address (private, for your own records only)</label>
          <input id="address" value={form.address} onChange={set("address")} />
        </div>
        <div className="form-row">
          <label htmlFor="pickup_notes">Pickup notes (e.g. "text before coming, apt 3B")</label>
          <textarea id="pickup_notes" value={form.pickup_notes} onChange={set("pickup_notes")} />
        </div>
        <div className="btn-row">
          <button type="submit" disabled={saving}>
            {saving ? "Saving..." : "Save"}
          </button>
          {savedAt && <span className="help-text">Saved.</span>}
        </div>
      </form>
    </div>
  );
}
