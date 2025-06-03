import { useContext } from "react";
import { Link, useHistory, useLocation } from "react-router-dom";
import { AuthContext } from "../context/AuthContext";
import PropylonLogo from "./PropylonLogo";
import dayjs from "dayjs";

const Layout = ({ children }) => {
  const { logout } = useContext(AuthContext);
  const history = useHistory();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    history.push("/login");
  };

  const isActiveRoute = (path) => {
    return location.pathname === path;
  };

  return (
    <div className="layout-wrapper">
      <nav className="navbar">
        <div className="container">
          <div className="navbar-brand">
            <PropylonLogo />
          </div>
          
          <div className="navbar-nav">
            <div className="navbar-start">
              <Link 
                to="/" 
                className={`navbar-link ${isActiveRoute('/') ? 'active' : ''}`}
              >
                My Files
              </Link>
              <Link 
                to="/shared" 
                className={`navbar-link ${isActiveRoute('/shared') ? 'active' : ''}`}
              >
                Shared with me
              </Link>
              <Link 
                to="/upload" 
                className={`navbar-link ${isActiveRoute('/upload') ? 'active' : ''}`}
              >
                Upload
              </Link>
            </div>
            
            <div className="navbar-end">
              <button className="btn btn-light btn-small" onClick={handleLogout}>
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="main-section">
        <div className="container">
          {children}
        </div>
      </main>

      <footer className="footer">
        <p>&copy; {dayjs().format("YYYY")} Propylon Document Manager</p>
      </footer>
    </div>
  );
};

export default Layout;