import React from "react";
import { BrowserRouter as Router, Route, Switch, Redirect } from "react-router-dom";

import LoginPage from "./pages/LoginPage";
import MyFilesPage from "./pages/MyFilesPage";
import SharedWithMePage from "./pages/SharedWithMePage";
import UploadPage from "./pages/UploadPage";
import FilePage from "./pages/FilePage";
import CompareVersionsPage from "./pages/CompareVersionsPage";
import { AuthProvider } from "./context/AuthContext";
import PrivateRoute from "./context/PrivateRoute";

function App() {
  return (
    <AuthProvider>
      <Router>
        <Switch>
          <Route exact path="/login" component={LoginPage} />
          <PrivateRoute exact path="/" Component={MyFilesPage} />
          <PrivateRoute path="/shared" Component={SharedWithMePage} />
          <PrivateRoute path="/upload" Component={UploadPage} />
          <PrivateRoute path="/file/:id" Component={FilePage} />
          <PrivateRoute path="/compare/:fileId" Component={CompareVersionsPage} />
          <Redirect to="/" />
        </Switch>
      </Router>
    </AuthProvider>
  );
}

export default App;