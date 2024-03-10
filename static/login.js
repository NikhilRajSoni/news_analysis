import { initializeApp } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-app.js";
import { getAnalytics } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-analytics.js";
import { getAuth ,GoogleAuthProvider,signInWithPopup} from "https://www.gstatic.com/firebasejs/10.8.0/firebase-auth.js";
    
const firebaseConfig = {
    apiKey: "AIzaSyAmAcaOLPk_GMffu63w1NoT41XAgwMX_B0",
    authDomain: "the-indian-express-dc526.firebaseapp.com",
    projectId: "the-indian-express-dc526",
    storageBucket: "the-indian-express-dc526.appspot.com",
    messagingSenderId: "619151524453",
    appId: "1:619151524453:web:5404c37b71791adc46fc8c",
    measurementId: "G-8DFV744PEQ"
  };

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);
const provider = new GoogleAuthProvider();
const auth = getAuth(app);
auth.languageCode = 'en'
const googleLogin = document.getElementById("google-login-btn");
googleLogin.addEventListener("click", function() {
    signInWithPopup(auth, provider)
        .then((result) => {
            const credential = GoogleAuthProvider.credentialFromResult(result);
            const token = credential.accessToken;
            const user = result.user;
            
            if (user.email === "su-23023@sitare.org") {
                window.location.href = "../templates/admin.html";
            } else{         
            window.location.href = "../templates/index.html";
            }
        })
        .catch((error) => {
            const errorCode = error.code;
            const errorMessage = error.message;
            const email = error.customData.email;
            const credential = GoogleAuthProvider.credentialFromError(error);
        });
});
