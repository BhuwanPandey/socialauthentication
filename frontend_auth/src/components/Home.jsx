import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

function Home() {
  const [user, setUser] = useState(null);
  //   const [istoken, setIstoken] = useState(false);
  const navigate = useNavigate();

  const GOOGLELOGIN_API = import.meta.env.VITE_GOOGLELOGIN;
  const GITHUBLOGIN_API = import.meta.env.VITE_GITHUBLOGIN;
  const USERME_API = import.meta.env.VITE_USERME;
  const REFRESHTOKEN_API = import.meta.env.VITE_REFRESHTOKEN;
  const BLACKLIST_API = import.meta.env.VITE_REFRESHBLACKLIST;
  const param = new URLSearchParams(window.location.search);
  const code = param.get("code")

  useEffect(() => {
    const token = JSON.parse(localStorage.getItem("auth_token"));
    const REFRESH_INTERVAL = 1000 * 60 * 4; // 4 minutes
    const hashParams = new URLSearchParams(window.location.hash.substring(1));
    const accessToken = hashParams.get("access_token");

    if (accessToken || code) {
      const loginData = accessToken
      ? { url: GOOGLELOGIN_API, request: { access_token: accessToken } }
      : { url: GITHUBLOGIN_API, request: { code:code } };
        handleLogin(loginData);
    } else if (token) {
      fetchUserProfile(token);
    } else {
      navigate("/login");
    }
    const intervalId = setInterval(() => {
      const token = JSON.parse(localStorage.getItem("auth_token"));
      if (token?.refresh) {
        updateToken(token);
      }
    }, REFRESH_INTERVAL);

    return () => clearInterval(intervalId);
  }, []);

  const fetchUserProfile = async (token) => {
    try {
      const response = await fetch(USERME_API, {
        headers: {
          Authorization: `Bearer ${token?.access}`,
        },
      });
      const data = await response.json();
      setUser(data);
    } catch {
      navigate("/login");
    }
  };

  const handleLogin = async (props) => {
    try {
      const response = await fetch(props.url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(props.request),
      });

      const data = await response.json();
      if (data.refresh) {
        localStorage.setItem("auth_token", JSON.stringify(data));
        window.history.replaceState(null, "", "/");
        fetchUserProfile(data);
        navigate("/");
      } else {
        navigate("/login");
      }
    } catch {
      navigate("/login");
    }
  };

  const blacklisttoken = async (token) => {
    try {
      await fetch(BLACKLIST_API, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh: token?.refresh }),
      });
    } catch (err) {
      console.error("Error blacklisting token:", err);
    }
  };

  const updateToken = async (token) => {
    try {
      const response = await fetch(REFRESHTOKEN_API, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh: token?.refresh }),
      });

      const data = await response.json();
      if (response.status === 200) {
        const updatedToken = { ...token, access: data.access };
        localStorage.setItem("auth_token", JSON.stringify(updatedToken));
      } else {
        logout();
      }
    } catch {
      logout();
    }
  };

  const logout = () => {
    const token = JSON.parse(localStorage.getItem("auth_token"));
    localStorage.removeItem("auth_token");
    blacklisttoken(token);
    navigate("/login");
  };

  if (!user) return <p>Loading...</p>;

  return (
    <div className="profile">
      <img src={user.image} alt="userprofile" className="profile-image" />
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
