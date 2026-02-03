import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  // Keep it small for class + local laptop
  vus: 10,              // virtual users
  duration: "15s",      // how long to run

  thresholds: {
    http_req_failed: ["rate<0.01"],     // < 1% requests can fail
    http_req_duration: ["p(95)<500"],   // 95% of requests < 500ms
  },
};

const BASE_URL = __ENV.BASE_URL || "http://127.0.0.1:5000";

export default function () {
  const res = http.get(`${BASE_URL}/dishes`);

  check(res, {
    "status is 200": (r) => r.status === 200,
    "returns json": (r) => (r.headers["Content-Type"] || "").includes("application/json"),
  });

  sleep(1);
}
