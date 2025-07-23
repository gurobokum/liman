"use client";
import { motion } from "framer-motion";
import { Book } from "lucide-react";

import { Button } from "@/src/components/ui/button";
import { Card } from "@/src/components/ui/card";

const steps = [
  {
    title: "Install SDK",
    command: "pip install liman",
  },
];

export default function GettingStarted() {
  return (
    <section id="getting-started" className="py-20 bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          className="text-center mb-16"
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <h2 className="text-3xl sm:text-4xl font-bold text-foreground mb-4">
            Quick Start
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            Build your first AI agent in minutes
          </p>
        </motion.div>

        <Card className="max-w-4xl mx-auto text-left">
          <motion.div
            className="p-8"
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <div className="space-y-6">
              {steps.map((step, index) => (
                <motion.div
                  key={index + 1}
                  className="flex items-start space-x-4"
                  initial={{ opacity: 0, x: -30 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                >
                  <div className="w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center font-semibold text-sm flex-shrink-0">
                    {index + 1}
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-foreground mb-2">
                      {step.title}
                    </h3>
                    <div className="bg-foreground rounded-lg p-4">
                      <code className="text-green-400 dark:text-green-800 font-mono text-sm">
                        {step.command}
                      </code>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>

            <motion.div
              className="mt-8 text-center"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.4 }}
            >
              <Button className="bg-primary hover:bg-primary/90 px-8 py-4 text-lg cursor-pointer">
                <Book className="mr-2 w-5 h-5" />
                View Documentation
              </Button>
            </motion.div>
          </motion.div>
        </Card>
      </div>
    </section>
  );
}
