import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

function Login() {
    const token = localStorage.getItem('auth_token');
    const navigate = useNavigate();

    useEffect(()=>{
        if(token){
            navigate("/")
        }
    },[])
    
    const loginWithGoogle = () => {
        window.location.href = import.meta.env.VITE_GOOGLE_LINK;
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