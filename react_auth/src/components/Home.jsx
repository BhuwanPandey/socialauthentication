import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

function Home() {
  const [user, setUser] = useState(null);
  const navigate = useNavigate();

  const GITHUB_CALLBACK = import.meta.env.VITE_GITHUB_CALLBACK;
  const USERME_API = import.meta.env.VITE_USERME;

  useEffect(() => {
    const token = JSON.parse(localStorage.getItem("auth_token"));
    const queryParams = new URLSearchParams(window.location.search);
    const code = queryParams.get("code");
    const state = queryParams.get("state");

    if (code && state) {
      handleGoogleLogin(code,state);
    } else if (token) {
      fetchUserProfile(token);
    } else {
      navigate("/login");
    }

  }, []);

  const fetchUserProfile = async (token) => {
    try {
      const response = await fetch(USERME_API, {
        headers: {
          Authorization: `Bearer ${token?.access_token}`,
        },
      });
      const data = await response.json();
      setUser(data);
    } catch {
      navigate("/login");
    }
  };

  const handleGoogleLogin = async (code,state) => {
    try {
      const callbackURL = `${GITHUB_CALLBACK}?code=${code}&state=${state}`;
      const response = await fetch(callbackURL, {
        headers: { "Content-Type": "application/json" },
      });

      const data = await response.json();

      if (data.access_token) {
        localStorage.setItem("auth_token", JSON.stringify(data));
        window.history.replaceState(null, "", "/");
        fetchUserProfile(data)
        navigate("/");
      } else {
        navigate("/login");
      }
    } catch {
      navigate("/login");
    }
  };


  const logout = () => {
    localStorage.removeItem("auth_token");
    navigate("/login");
  };

  if (!user) return <p>Loading...</p>;

  return (
    <div className="profile">
      <img src={user.avatar} alt="userprofile" className="profile-image" />
      <div className="profile-details">
        <div className="user_name">
          Name: <span>{user.username}</span>
        </div>
        <div className="user_email">
          Email: <span>{user.email}</span>
        </div>
        <br />
        <button onClick={logout}>Sign out</button>
      </div>
    </div>
  );
}

export default Home;