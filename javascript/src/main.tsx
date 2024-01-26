import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import sdk_framework from '../public/sdk_framework.png';

ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
        <img src={sdk_framework} alt="SDK Framework" />
    </React.StrictMode>
);
