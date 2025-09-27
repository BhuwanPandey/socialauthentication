import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

function Login() {
    const token = localStorage.getItem('auth_token');
    const navigate = useNavigate();
    const VITE_GOOGLE_AUTHORIZE = import.meta.env.VITE_GOOGLE_AUTHORIZE;

    useEffect(()=>{
        if(token){
            navigate("/")
        }
    },[])
    
    const loginWithGoogle = async() => {
        try{
            const response = await fetch(VITE_GOOGLE_AUTHORIZE);
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
        <button onClick={loginWithGoogle} >
        <i className="fa fa-google" aria-hidden="true"></i>
        Sign in with Google
        </button>
    </div>
    </>
    );
}

export default Login