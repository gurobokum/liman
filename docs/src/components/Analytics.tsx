"use client";
import { Analytics as VercelAnalytics } from "@vercel/analytics/next";

export default function Analytics() {
  return (
    <VercelAnalytics
      beforeSend={(event) => {
        if (localStorage.getItem("va-disable") === "true") {
          console.log("Vercel analytics disabled");
          return null; // Disable analytics if the flag is set
        }
        return event;
      }}
    />
  );
}
