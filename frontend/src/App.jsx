import { NavLink, Route, Routes } from "react-router-dom";
import ItemDetailPage from "./pages/ItemDetailPage.jsx";
import ItemsPage from "./pages/ItemsPage.jsx";
import SellerProfilePage from "./pages/SellerProfilePage.jsx";

export default function App() {
  return (
    <div className="app-shell">
      <header className="top-nav">
        <div className="brand">📦 Marketplace Seller Assistant</div>
        <nav>
          <NavLink to="/" end className={({ isActive }) => (isActive ? "active" : "")}>
            Items
          </NavLink>
          <NavLink to="/profile" className={({ isActive }) => (isActive ? "active" : "")}>
            Seller Profile
          </NavLink>
        </nav>
      </header>
      <Routes>
        <Route path="/" element={<ItemsPage />} />
        <Route path="/profile" element={<SellerProfilePage />} />
        <Route path="/items/:id" element={<ItemDetailPage />} />
      </Routes>
    </div>
  );
}
