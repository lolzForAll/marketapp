import { Link } from "react-router-dom";

const STATUS_LABEL = {
  draft: "Draft",
  analyzed: "Priced",
  approved: "Approved",
  publish_started: "Publishing",
  posted: "Posted",
};

export default function ItemCard({ item }) {
  const cover = item.photos[0]?.url;
  const price = item.price_final ?? item.price_suggested;
  return (
    <Link to={`/items/${item.id}`} className="item-card">
      {cover ? <img src={cover} alt={item.title} /> : <div style={{ height: 160, background: "#eee" }} />}
      <div className="body">
        <div className="title">{item.title || "(untitled)"}</div>
        <div className="price">{price != null ? `$${price}` : "no price yet"}</div>
        <span className={`badge ${item.status}`}>{STATUS_LABEL[item.status] || item.status}</span>
      </div>
    </Link>
  );
}
