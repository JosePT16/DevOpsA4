import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  vus: 10,              
  duration: "15s",      

  thresholds: {
    http_req_failed: ["rate<0.01"],    
    http_req_duration: ["p(95)<500"],  
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
