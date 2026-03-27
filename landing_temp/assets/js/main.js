/**
* Template Name: FlexStart
* Template URL: https://bootstrapmade.com/flexstart-bootstrap-startup-template/
* Updated: Nov 01 2024 with Bootstrap v5.3.3
* Author: BootstrapMade.com
* License: https://bootstrapmade.com/license/
*/

(function() {
  "use strict";

  /**
   * Apply .scrolled class to the body as the page is scrolled down
   */
  function toggleScrolled() {
    const selectBody = document.querySelector('body');
    const selectHeader = document.querySelector('#header');
    if (!selectHeader.classList.contains('scroll-up-sticky') && !selectHeader.classList.contains('sticky-top') && !selectHeader.classList.contains('fixed-top')) return;
    window.scrollY > 100 ? selectBody.classList.add('scrolled') : selectBody.classList.remove('scrolled');
  }

  document.addEventListener('scroll', toggleScrolled);
  window.addEventListener('load', toggleScrolled);

  /**
   * Mobile nav toggle
   */
  const mobileNavToggleBtn = document.querySelector('.mobile-nav-toggle');

  function mobileNavToogle() {
    document.querySelector('body').classList.toggle('mobile-nav-active');
    mobileNavToggleBtn.classList.toggle('bi-list');
    mobileNavToggleBtn.classList.toggle('bi-x');
  }
  if (mobileNavToggleBtn) {
    mobileNavToggleBtn.addEventListener('click', mobileNavToogle);
  }

  /**
   * Hide mobile nav on same-page/hash links
   */
  document.querySelectorAll('#navmenu a').forEach(navmenu => {
    navmenu.addEventListener('click', () => {
      if (document.querySelector('.mobile-nav-active')) {
        mobileNavToogle();
      }
    });

  });

  /**
   * Toggle mobile nav dropdowns
   */
  document.querySelectorAll('.navmenu .toggle-dropdown').forEach(navmenu => {
    navmenu.addEventListener('click', function(e) {
      e.preventDefault();
      this.parentNode.classList.toggle('active');
      this.parentNode.nextElementSibling.classList.toggle('dropdown-active');
      e.stopImmediatePropagation();
    });
  });

  /**
   * Scroll top button
   */
  let scrollTop = document.querySelector('.scroll-top');

  function toggleScrollTop() {
    if (scrollTop) {
      window.scrollY > 100 ? scrollTop.classList.add('active') : scrollTop.classList.remove('active');
    }
  }
  scrollTop.addEventListener('click', (e) => {
    e.preventDefault();
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  });

  window.addEventListener('load', toggleScrollTop);
  document.addEventListener('scroll', toggleScrollTop);

  /**
   * Animation on scroll function and init
   */
  function aosInit() {
    AOS.init({
      duration: 600,
      easing: 'ease-in-out',
      once: true,
      mirror: false
    });
  }
  window.addEventListener('load', aosInit);

  /**
   * Initiate glightbox
   */
  const glightbox = GLightbox({
    selector: '.glightbox'
  });

  /**
   * Initiate Pure Counter
   */
  new PureCounter();

  /**
   * Frequently Asked Questions Toggle
   */
  document.querySelectorAll('.faq-item h3, .faq-item .faq-toggle').forEach((faqItem) => {
    faqItem.addEventListener('click', () => {
      faqItem.parentNode.classList.toggle('faq-active');
    });
  });

  /**
   * Init isotope layout and filters
   */
  document.querySelectorAll('.isotope-layout').forEach(function(isotopeItem) {
    let layout = isotopeItem.getAttribute('data-layout') ?? 'masonry';
    let filter = isotopeItem.getAttribute('data-default-filter') ?? '*';
    let sort = isotopeItem.getAttribute('data-sort') ?? 'original-order';

    let initIsotope;
    imagesLoaded(isotopeItem.querySelector('.isotope-container'), function() {
      initIsotope = new Isotope(isotopeItem.querySelector('.isotope-container'), {
        itemSelector: '.isotope-item',
        layoutMode: layout,
        filter: filter,
        sortBy: sort
      });
    });

    isotopeItem.querySelectorAll('.isotope-filters li').forEach(function(filters) {
      filters.addEventListener('click', function() {
        isotopeItem.querySelector('.isotope-filters .filter-active').classList.remove('filter-active');
        this.classList.add('filter-active');
        initIsotope.arrange({
          filter: this.getAttribute('data-filter')
        });
        if (typeof aosInit === 'function') {
          aosInit();
        }
      }, false);
    });

  });

  /**
   * Init swiper sliders
   */
  function initSwiper() {
    document.querySelectorAll(".init-swiper").forEach(function(swiperElement) {
      let config = JSON.parse(
        swiperElement.querySelector(".swiper-config").innerHTML.trim()
      );

      if (swiperElement.classList.contains("swiper-tab")) {
        initSwiperWithCustomPagination(swiperElement, config);
      } else {
        new Swiper(swiperElement, config);
      }
    });
  }

  window.addEventListener("load", initSwiper);

  /**
   * Correct scrolling position upon page load for URLs containing hash links.
   */
  window.addEventListener('load', function(e) {
    if (window.location.hash) {
      if (document.querySelector(window.location.hash)) {
        setTimeout(() => {
          let section = document.querySelector(window.location.hash);
          let scrollMarginTop = getComputedStyle(section).scrollMarginTop;
          window.scrollTo({
            top: section.offsetTop - parseInt(scrollMarginTop),
            behavior: 'smooth'
          });
        }, 100);
      }
    }
  });

  /**
   * Navmenu Scrollspy
   */
  let navmenulinks = document.querySelectorAll('.navmenu a');

  function navmenuScrollspy() {
    navmenulinks.forEach(navmenulink => {
      if (!navmenulink.hash) return;
      let section = document.querySelector(navmenulink.hash);
      if (!section) return;
      let position = window.scrollY + 200;
      if (position >= section.offsetTop && position <= (section.offsetTop + section.offsetHeight)) {
        document.querySelectorAll('.navmenu a.active').forEach(link => link.classList.remove('active'));
        navmenulink.classList.add('active');
      } else {
        navmenulink.classList.remove('active');
      }
    })
  }
  window.addEventListener('load', navmenuScrollspy);
  document.addEventListener('scroll', navmenuScrollspy);

  /**
   * Service Details Page
   */
  const serviceDetailsPage = document.querySelector('.service-details-page');

  if (serviceDetailsPage) {
    const serviceContent = {
      'custom-software': {
        title: 'From Idea to Scalable Digital Product',
        image: 'assets/img/services.jpg',
        description: `
          <p>Custom software development is our core offering. We build solutions from the ground up to meet your specific business needs, acting as your technology partner to turn a concept into a successful, scalable digital product.</p>
          <ul>
            <li><i class="bi bi-check-circle"></i> <strong>Web Application Development:</strong> Creating powerful applications that run in a web browser, such as customer portals, e-commerce platforms, and SaaS products.</li>
            <li><i class="bi bi-check-circle"></i> <strong>Mobile App Development:</strong> Designing native (iOS/Android) and cross-platform mobile apps for smartphones and tablets.</li>
            <li><i class="bi bi-check-circle"></i> <strong>Enterprise Software Solutions:</strong> Building comprehensive software like CRM and ERP systems to help large organizations manage operations and automate processes.</li>
          </ul>
          <p>Our collaborative approach, combined with Agile and DevOps methodologies, ensures transparency and delivers targeted results. We select the right technologies to fit your requirements, ensuring a timely and cost-effective delivery.</p>
        `
      },
      'tech-consulting': {
        title: 'Technology Consulting & IT Strategy',
        image: 'assets/img/blog/blog-1.jpg',
        description: `
          <p>We provide expert advice to help businesses make informed decisions about their technology and digital direction.</p>
          <ul>
            <li><i class="bi bi-check-circle"></i> <strong>Digital Transformation:</strong> Guiding businesses on how to modernize their legacy systems and integrate digital technology into all areas of their operations.</li>
            <li><i class="bi bi-check-circle"></i> <strong>Technology Roadmap Planning:</strong> Creating a strategic plan for a company's technology adoption, implementation, and maintenance over time.</li>
            <li><i class="bi bi-check-circle"></i> <strong>Software Architecture Review & Design:</strong> Assessing the foundation of a client's existing software or designing a robust and scalable architecture for a new project.</li>
            <li><i class="bi bi-check-circle"></i> <strong>Feasibility and Risk Analysis:</strong> We help you evaluate the technical feasibility of your project and identify potential risks before development begins.</li>
          </ul>
        `
      },
      'ui-ux': {
        title: 'Engaging and Intuitive UI/UX Design',
        image: 'assets/img/blog/blog-2.jpg',
        description: `
          <p>We craft intuitive, engaging, and aesthetically pleasing digital experiences for users.</p>
          <ul>
            <li><i class="bi bi-check-circle"></i> <strong>User Experience (UX) Design:</strong> Researching user behavior to map out the user journey, create wireframes, and ensure the product is logical and easy to navigate.</li>
            <li><i class="bi bi-check-circle"></i> <strong>User Interface (UI) Design:</strong> Designing the visual elements of the application, including layouts, color schemes, typography, and interactive elements.</li>
            <li><i class="bi bi-check-circle"></i> <strong>Prototyping & User Testing:</strong> Building interactive mockups to test with real users and gather feedback before full development begins.</li>
            <li><i class="bi bi-check-circle"></i> <strong>Brand Identity Integration:</strong> Ensuring your software's design is a seamless extension of your brand identity for a cohesive user experience.</li>
          </ul>
        `
      },
      'cloud-devops': {
        title: 'Cloud & DevOps Services',
        image: 'assets/img/blog/blog-3.jpg',
        description: `
          <p>Helping companies leverage cloud computing and streamline their development processes for faster and more reliable software delivery.</p>
          <ul>
            <li><i class="bi bi-check-circle"></i> <strong>Cloud Migration & Management:</strong> Assisting businesses in moving their infrastructure to platforms like AWS, Azure, or GCP.</li>
            <li><i class="bi bi-check-circle"></i> <strong>DevOps & CI/CD:</strong> Implementing practices and tools that automate the process of building, testing, and deploying software.</li>
            <li><i class="bi bi-check-circle"></i> <strong>Cloud-Native Development:</strong> Building applications designed to take full advantage of cloud architecture for superior performance and scalability.</li>
            <li><i class="bi bi-check-circle"></i> <strong>Infrastructure as Code (IaC):</strong> Managing and provisioning infrastructure through code for consistency and reliability.</li>
          </ul>
        `
      },
      'digital-marketing': {
        title: 'Digital Marketing & SEO',
        image: 'assets/img/blog/blog-4.jpg',
        description: `
          <p>Boost your online presence and reach your target audience with our comprehensive digital marketing services.</p>
          <ul>
            <li><i class="bi bi-check-circle"></i> <strong>Search Engine Optimization (SEO):</strong> Improving your website's visibility on search engines to attract organic traffic.</li>
            <li><i class="bi bi-check-circle"></i> <strong>Social Media Promotion:</strong> Managing and growing your presence on platforms like Instagram, Facebook, and YouTube.</li>
            <li><i class="bi bi-check-circle"></i> <strong>Content Creation:</strong> Developing engaging content, from blog posts to videos, that resonates with your audience and supports your brand.</li>
            <li><i class="bi bi-check-circle"></i> <strong>Paid Advertising (PPC):</strong> Managing targeted ad campaigns on Google and social media to drive immediate traffic and leads.</li>
          </ul>
        `
      },
      'support-maintenance': {
        title: 'Ongoing Support & Maintenance',
        image: 'assets/img/blog/blog-recent-1.jpg',
        description: `
          <p>Ensuring that your software applications continue to run smoothly and evolve after they are launched.</p>
          <ul>
            <li><i class="bi bi-check-circle"></i> <strong>Application Maintenance:</strong> Providing regular updates, bug fixes, and performance enhancements.</li>
            <li><i class="bi bi-check-circle"></i> <strong>Technical Support:</strong> Offering dedicated support to help clients and their users resolve technical issues.</li>
            <li><i class="bi bi-check-circle"></i> <strong>System Monitoring:</strong> Proactively monitoring application performance and security to prevent downtime and data breaches.</li>
            <li><i class="bi bi-check-circle"></i> <strong>Scalability & Feature Enhancements:</strong> Helping your application evolve with new features and scale to meet growing user demand.</li>
          </ul>
        `
      },
      'billing-software': {
        title: 'GST Billing Software for Small Businesses',
        image: 'assets/img/values-1.png',
        description: `
          <p>Empower your small business with our intuitive and powerful GST billing software. Designed for simplicity and efficiency, it helps you manage invoices, track inventory, and stay compliant with GST regulations effortlessly.</p>
          <ul>
            <li><i class="bi bi-check-circle"></i> <strong>Easy Invoicing:</strong> Create and send professional, GST-compliant invoices in minutes.</li>
            <li><i class="bi bi-check-circle"></i> <strong>Inventory Management:</strong> Keep track of your stock levels automatically as you make sales and purchases.</li>
            <li><i class="bi bi-check-circle"></i> <strong>GST Compliance:</strong> Generate accurate GST reports (GSTR-1, GSTR-3B) and file your returns without hassle.</li>
            <li><i class="bi bi-check-circle"></i> <strong>Business Dashboards:</strong> Get a clear overview of your business performance with insightful reports and analytics.</li>
          </ul>
        `
      },
      'pos-application': {
        title: 'Modern Point-of-Sale (POS) Applications',
        image: 'assets/img/portfolio/app-1.jpg',
        description: `
          <p>Our POS applications are designed for speed, reliability, and ease of use, helping you streamline sales and manage your business efficiently.</p>
          <ul>
            <li><i class="bi bi-check-circle"></i> <strong>Fast Checkout:</strong> Process transactions quickly to reduce wait times and improve customer satisfaction.</li>
            <li><i class="bi bi-check-circle"></i> <strong>Inventory Sync:</strong> Automatically update your inventory with every sale, preventing stockouts and overstocking.</li>
            <li><i class="bi bi-check-circle"></i> <strong>Sales Analytics:</strong> Track sales trends, identify best-selling products, and make data-driven business decisions.</li>
            <li><i class="bi bi-check-circle"></i> <strong>Multi-Platform Support:</strong> Our POS solutions can be deployed on desktops, tablets, and mobile devices.</li>
          </ul>
        `
      },
      'digital-menu': {
        title: 'Interactive Digital Menus',
        image: 'assets/img/portfolio/app-2.jpg',
        description: `
          <p>Replace traditional paper menus with an engaging, interactive digital menu that can be updated instantly.</p>
          <ul>
            <li><i class="bi bi-check-circle"></i> <strong>Easy Updates:</strong> Instantly change menu items, prices, and specials without reprinting.</li>
            <li><i class="bi bi-check-circle"></i> <strong>Visually Appealing:</strong> Showcase your dishes with high-quality images and enticing descriptions.</li>
            <li><i class="bi bi-check-circle"></i> <strong>Contactless Ordering:</strong> Allow customers to browse and order directly from their own devices via a QR code.</li>
            <li><i class="bi bi-check-circle"></i> <strong>Increased Sales:</strong> Promote specials and upsell items with eye-catching visuals and recommendations.</li>
          </ul>
        `
      }
    };

    const serviceLinks = document.querySelectorAll('.services-list a');
    const serviceContentContainer = document.getElementById('service-content');

    serviceLinks.forEach(link => {
      link.addEventListener('click', function(e) {
        e.preventDefault();

        // Remove active class from all links
        serviceLinks.forEach(l => l.classList.remove('active'));

        // Add active class to the clicked link
        this.classList.add('active');

        const serviceKey = this.getAttribute('data-service');
        const content = serviceContent[serviceKey];

        if (content && serviceContentContainer) {
          const contentHTML = `
            <img src="${content.image}" alt="" class="img-fluid services-img">
            <h3>${content.title}</h3>
            ${content.description}
          `;
          serviceContentContainer.innerHTML = contentHTML;

          // Smooth scroll to the top of the content area
          serviceContentContainer.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
          });
          // Re-initialize AOS for the new content
          if (typeof AOS !== 'undefined') {
            AOS.refresh();
          }
        }
      });
    });
  }

})();