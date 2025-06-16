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
    
    const loginWithGithub = () => {
        window.location.href = import.meta.env.VITE_GITHUB_LINK;
    };

    const loginWithGoogle = () => {
        window.location.href = import.meta.env.VITE_GOOGLE_LINK;
    };

return (
    <>
    <div className="auth_button">
        <button onClick={loginWithGithub} style={{"background":"blue"}}>
            <i className="fa fa-github" aria-hidden="true"></i>
            Sign in with Github
        </button>

        <button onClick={loginWithGoogle} >
            <i className="fa fa-google" aria-hidden="true"></i>
            Sign in with Google
        </button>
    </div>
    </>
    );
}

export default Login