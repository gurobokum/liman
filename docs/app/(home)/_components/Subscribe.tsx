"use client";
import { motion } from "framer-motion";
import { ArrowRight, CheckCircle, Mail } from "lucide-react";
import React, { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/src/components/ui/button";
import { Input } from "@/src/components/ui/input";

export default function Subscribe() {
  const [email, setEmail] = useState("");
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!email) {
      toast.error("Email required", {
        description: "Please enter your email address",
        position: "top-center",
      });
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      toast.error("Invalid email", {
        description: "Please enter a valid email address",
        position: "top-center",
      });
      return;
    }

    setIsLoading(true);

    const res = await fetch("/api/subscribe", {
      body: JSON.stringify({ email }),
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });

    if (!res.ok) {
      setIsLoading(false);
      const error = await res.text();
      toast.error("Subscription failed", {
        description: error || "Something went wrong. Please try again later.",
        position: "top-center",
      });
      return;
    }

    setIsSubscribed(true);
    setIsLoading(false);

    toast.success("Successfully subscribed!", {
      description: "You'll receive updates about Liman development",
      position: "top-center",
    });

    setEmail("");
  };

  return (
    <section className="pt-20 pb-25 border-t border-b">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <div className="mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-primary/10 rounded-full mb-6">
              <Mail className="w-8 h-8 text-primary" />
            </div>
            <h2 className="text-3xl sm:text-4xl font-bold text-foreground mb-4">
              Stay Updated
            </h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Get the latest updates on Liman development, new features, and
              best practices delivered to your inbox.
            </p>
          </div>

          {!isSubscribed ? (
            <motion.form
              onSubmit={handleSubmit}
              className="flex flex-col sm:flex-row gap-4 max-w-md mx-auto"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.2 }}
            >
              <Input
                type="email"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="flex-1"
                disabled={isLoading}
              />
              <Button
                type="submit"
                disabled={isLoading}
                className="bg-primary hover:bg-primary/90 px-6"
              >
                {isLoading ? (
                  "Subscribing..."
                ) : (
                  <>
                    Subscribe
                    <ArrowRight className="ml-2 w-4 h-4" />
                  </>
                )}
              </Button>
            </motion.form>
          ) : (
            <motion.div
              className="flex items-center justify-center gap-3 text-green-600"
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5 }}
            >
              <CheckCircle className="w-6 h-6" />
              <span className="text-lg font-medium">
                Thank you for subscribing!
              </span>
            </motion.div>
          )}

          <motion.p
            className="text-sm text-muted-foreground mt-4"
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.4 }}
          >
            No spam, unsubscribe at any time. We respect your privacy.
          </motion.p>
        </motion.div>
      </div>
    </section>
  );
}
