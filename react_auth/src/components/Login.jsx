import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

function Login() {
    const token = localStorage.getItem('auth_token');
    const navigate = useNavigate();
    const VITE_GITHUB_AUTHORIZE = import.meta.env.VITE_GITHUB_AUTHORIZE;

    useEffect(()=>{
        if(token){
            navigate("/")
        }
    },[])
    
    const loginWithGithub = async() => {
        try{
            const response = await fetch(VITE_GITHUB_AUTHORIZE);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            const authorizationUrl  = data.authorization_url ;
            if (authorizationUrl) {
                window.location.href = authorizationUrl;
            } else {
                console.error("Authorization URL not found in response.");
            }
        }
        catch(err){
            console.log("Login with Google failed:",err)
        }
    };

return (
    <>
    <div className="auth_button">
        <button onClick={loginWithGithub} style={{"background":"blue"}}>
            <i className="fa fa-github" aria-hidden="true"></i>
            Sign in with Github
        </button>
    </div>
    </>
    );
}

export default Login