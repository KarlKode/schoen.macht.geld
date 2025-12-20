import type { SVGProps } from 'react';

export function Logo(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      {/* Disco Ball Sphere */}
      <circle cx="12" cy="12" r="10" fill="currentColor" opacity="0.1" />
      <circle cx="12" cy="12" r="10" strokeWidth="1.5"/>

      {/* Facet Grid Lines */}
      <path d="M12 2a15 15 0 0 0 -5 20" />
      <path d="M12 2a15 15 0 0 1 5 20" />
      <path d="M2 12a15 15 0 0 0 20 5" />
      <path d="M2 12a15 15 0 0 1 20-5" />

      {/* Dollar Signs as facets */}
      <g strokeWidth="2.5" stroke="currentColor" fill="none">
        {/* Central Dollar Sign */}
        <path d="M12 15V9" />
        <path d="M13.5 10a1.5 1.5 0 0 0 -3 0" />
        <path d="M10.5 14a1.5 1.5 0 0 0 3 0" />
        {/* Smaller dollar signs */}
        <g transform="scale(0.5) translate(19 2)">
          <path d="M12 15V9" />
          <path d="M13.5 10a1.5 1.5 0 0 0 -3 0" />
          <path d="M10.5 14a1.5 1.5 0 0 0 3 0" />
        </g>
        <g transform="scale(0.5) translate(5 28)">
          <path d="M12 15V9" />
          <path d="M13.5 10a1.5 1.5 0 0 0 -3 0" />
          <path d="M10.5 14a1.5 1.5 0 0 0 3 0" />
        </g>
         <g transform="scale(0.4) translate(-10 18)">
          <path d="M12 15V9" />
          <path d="M13.5 10a1.5 1.5 0 0 0 -3 0" />
          <path d="M10.5 14a1.5 1.5 0 0 0 3 0" />
        </g>
      </g>
      
       {/* Sparkle */}
      <path d="M20 7 L 21 6" strokeWidth="1.5" />
      <path d="M19 4 L 18 3" strokeWidth="1" />

    </svg>
  );
}
