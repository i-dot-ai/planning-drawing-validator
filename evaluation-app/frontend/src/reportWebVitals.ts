import { onCLS, onINP, onFCP, onLCP, onTTFB } from "web-vitals";

/**
 * Reports web vitals metrics.
 * Metrics are captured but not logged by default.
 * Uncomment console.log lines to enable debug logging.
 */
export function reportWebVitals() {
  // Cumulative Layout Shift (CLS)
  // Good: < 0.1, Needs improvement: 0.1-0.25, Poor: > 0.25
  onCLS(() => {});

  // Interaction to Next Paint (INP) - replaces FID
  // Good: < 200ms, Needs improvement: 200-500ms, Poor: > 500ms
  onINP(() => {});

  // First Contentful Paint (FCP)
  // Good: < 1.8s, Needs improvement: 1.8-3s, Poor: > 3s
  onFCP(() => {});

  // Largest Contentful Paint (LCP)
  // Good: < 2.5s, Needs improvement: 2.5-4s, Poor: > 4s
  onLCP(() => {});

  // Time to First Byte (TTFB)
  // Good: < 800ms, Needs improvement: 800-1800ms, Poor: > 1800ms
  onTTFB(() => {});
}
