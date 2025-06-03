import { useForm } from "react-hook-form";
import { useState, useContext, useEffect, useRef } from "react";
import { useHistory } from "react-router-dom";
import api from "../api/client";
import { AuthContext } from "../context/AuthContext";
import dayjs from "dayjs";

import PropylonLogo from "../components/PropylonLogo";

function LoginPage() {
  const history = useHistory();
  const { token, login } = useContext(AuthContext);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  
  // Use ref to track if component is mounted
  const isMountedRef = useRef(true);

  useEffect(() => {
    // Set mounted to true when component mounts
    isMountedRef.current = true;
    
    if (token) {
      history.push("/");
    }
    
    // Cleanup function
    return () => {
      isMountedRef.current = false;
    };
  }, [token, history]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (isLoading) return; // Prevent multiple submissions
    
    setIsLoading(true);
    setError(null);

    try {
      const response = await api.post("/token/", { email, password });
      
      // Only update state if component is still mounted
      if (isMountedRef.current) {
        login(response.data.token);
        history.push("/");
      }
    } catch (err) {
      // Only update state if component is still mounted
      if (isMountedRef.current) {
        setError("Invalid credentials");
      }
    } finally {
      // Only update state if component is still mounted
      if (isMountedRef.current) {
        setIsLoading(false);
      }
    }
  };

  return (
    <div className="fullscreen-center">
      <div className="center-container">
        <div className="card fade-in">
          <div className="card-header">
            <PropylonLogo />
          </div>
          
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label" htmlFor="email">
                Email Address
              </label>
              <input
                id="email"
                className="form-input"
                type="email"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={isLoading}
                required
              />
            </div>
            
            <div className="form-group">
              <label className="form-label" htmlFor="password">
                Password
              </label>
              <input
                id="password"
                className="form-input"
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={isLoading}
                required
              />
            </div>
            
            {error && (
              <div className="alert alert-danger mb-4">
                {error}
              </div>
            )}
            
            <div className="form-group">
              <button 
                className={`btn btn-primary btn-full ${isLoading ? 'btn-loading' : ''}`}
                type="submit"
                disabled={isLoading}
              >
                {isLoading ? 'Signing in...' : 'Sign In'}
              </button>
            </div>
          </form>
        </div>
        
        <p className="text-center text-grey text-xs mt-4">
          &copy; {dayjs().format("YYYY")} RWS. All rights reserved.
        </p>
      </div>
    </div>
  );
}

export default LoginPage;

