// @ts-check

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: "Scarfolder",
  tagline: "Data and file scaffolding via configurable YAML pipelines",
  favicon: "img/favicon.ico",

  // Update these to match your GitHub Pages setup.
  url: "https://freshmag.github.io",
  baseUrl: "/scarfolder-py/",
  organizationName: "FreshMag",
  projectName: "scarfolder-py",

  onBrokenLinks: "throw",
  onBrokenMarkdownLinks: "warn",

  i18n: {
    defaultLocale: "en",
    locales: ["en"],
  },

  presets: [
    [
      "classic",
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: "./sidebars.js",
          routeBasePath: "/",   // docs at root, no /docs/ prefix
          editUrl: "https://github.com/FreshMag/scarfolder-py/edit/main/docs/",
        },
        blog: false,            // no blog
        theme: {
          customCss: "./src/css/custom.css",
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      navbar: {
        title: "Scarfolder",
        items: [
          {
            type: "docSidebar",
            sidebarId: "docs",
            position: "left",
            label: "Docs",
          },
          {
            href: "https://github.com/FreshMag/scarfolder-py",
            label: "GitHub",
            position: "right",
          },
        ],
      },
      footer: {
        style: "dark",
        links: [
          {
            title: "Docs",
            items: [
              { label: "Getting Started", to: "/" },
              { label: "Concepts", to: "/concepts" },
              { label: "Configuration", to: "/configuration" },
              { label: "Built-in Plugins", to: "/plugins" },
              { label: "Custom Plugins", to: "/custom-plugins" },
            ],
          },
          {
            title: "More",
            items: [
              {
                label: "GitHub",
                href: "https://github.com/FreshMag/scarfolder-py",
              },
            ],
          },
        ],
        copyright: `Copyright © ${new Date().getFullYear()} Scarfolder. Built with Docusaurus.`,
      },
      prism: {
        additionalLanguages: ["bash", "yaml", "python", "docker"],
      },
    }),
};

export default config;
