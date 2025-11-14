require('dotenv').config();

const express = require('express');
const app = express();

// Use PORT from environment, default to 3001
const PORT = process.env.PORT || 3001;

// Placeholder for calling entservices-infra-712 in the future
const ENTSERVICES_URL = process.env.ENTSERVICES_INFRA_URL || 'http://localhost:3002';

// Health endpoint for monitoring
// PUBLIC_INTERFACE
app.get('/health', (req, res) => {
    /**
     * Returns the health status of the Thunder-712 backend.
     * Response:
     *   200 OK: { status: 'ok' }
     */
    res.status(200).json({ status: 'ok' });
});

// Example API endpoint
// PUBLIC_INTERFACE
app.get('/api/info', (req, res) => {
    /**
     * Minimal API endpoint returning basic service info.
     * Response:
     *   200 OK: { service: 'Thunder-712 backend', dependency: 'entservices-infra-712', entservices_url: ENTSERVICES_URL }
     */
    res.status(200).json({
        service: 'Thunder-712 backend',
        dependency: 'entservices-infra-712',
        entservices_url: ENTSERVICES_URL, // Reference for future use
    });
});

app.listen(PORT, () => {
    console.log(`Thunder-712 backend service running on port ${PORT}`);
    console.log(`(entservices-infra-712 URL placeholder: ${ENTSERVICES_URL})`);
});
