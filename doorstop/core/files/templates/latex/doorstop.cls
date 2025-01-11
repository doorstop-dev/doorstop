%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% LaTeX document class: doorstop.cls
%%
%% Derived from the Standard LaTeX Book article class.
%%
%% This document class is free to use, copy, distribute,
%% and modify, as long as reference to the original author
%% is given.
%%
%% Original author: Gustav Wulf, gustav@neer.se
%%
%% Last modified by: Gustav Wulf, December 29, 2023.
%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% ******************************************************
% Identification
% ******************************************************
\def\classversion{1.0}
\def\classdate{Dec 29, 2023}

\typeout{Document class version: \classversion}
\typeout{Last modified: \classdate}
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{template/doorstop}

% ******************************************************
% Declare Options
% ******************************************************
% Do not know how to handle other options and therefore
% just pass them on to 'article'
\DeclareOption{proofing}{\def\proof{1}}
% Make sure we can do bold typewriter
\DeclareFontShape{OT1}{cmtt}{bx}{n}{<5><6><7><8><9><10><10.95><12><14.4><17.28><20.74><24.88>cmttb10}{}
% Setup the hyperref package options
\PassOptionsToPackage{bookmarks=true,%
  bookmarksopen=true,%
  pdfborder={0 0 0},%
  pdfhighlight={/N},%
  linkbordercolor={.5 .5 .5},%
  raiselinks=true,%
  nesting=false}{hyperref}
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{article}}

% ******************************************************
% Process Options
% ******************************************************
\ProcessOptions*

% ******************************************************
% Improve error finding capabilities
% ******************************************************
\errorcontextlines 10000

% ******************************************************
% Load Used Packages and Classes
% ******************************************************
\LoadClass{article}
\RequirePackage{titletoc}
\RequirePackage{palatino}
\RequirePackage{graphicx}
\RequirePackage{fancyhdr}
\RequirePackage{multirow}
\RequirePackage{lastpage}
\RequirePackage{color}
\RequirePackage{listings}
\RequirePackage{tikz}
\RequirePackage{xstring}
\RequirePackage{titlesec}
\RequirePackage{appendix}
% The following packages are REQUIRED to make the Doorstop publish functions work.
\RequirePackage{amsmath}
\RequirePackage{ulem}
\RequirePackage{longtable}
\RequirePackage{fancyvrb}
\RequirePackage{xr-hyper}
\RequirePackage[unicode,colorlinks]{hyperref}
\RequirePackage{zref-user}
\RequirePackage{zref-xr}

% ******************************************************
% Functions for PlantUML support.
% ******************************************************
% Define an verbatim environment for PlantUML:
\newenvironment{plantuml}[1]{\VerbatimOut{#1.txt}}{\endVerbatimOut}

% Process a PlantUML code:
\newcommand{\process}[4]{%
    % Call PlantUML to produce a svg vector graphcis:
    \immediate\write18{plantuml -tsvg #1.txt}
    % Call Inkscape to convert the svg to a pdf (pdflatex cannot use svg):
    \immediate\write18{inkscape #1.svg --export-pdf=#1.pdf}
    % Include the pdf:
	\begin{figure}[!h]
		\includegraphics[width=#2]{#1.pdf}
        \caption{#3}
		\label{fig:plant#4}\zlabel{fig:plant#4}
    \end{figure}
    % Remove all intermediate files:
    \immediate\write18{rm #1.txt #1.svg #1.pdf}
}

% ******************************************************
% Start defining and redefining old article style stuff
% ******************************************************
% Setup the page margins
\setlength{\topmargin}{-2cm}
\setlength{\textwidth}{16cm}
\setlength{\textheight}{23cm}
\setlength{\evensidemargin}{-4.5mm}
\setlength{\oddsidemargin}{5.5mm}
\setlength{\intextsep}{24pt}
\setlength{\headheight}{3cm}
\setlength{\headwidth}{16cm}

% Define logotype and trim.
\newcommand{\definetrim}[2]{%
  \define@key{Gin}{#1}[]{\setkeys{Gin}{trim=#2,clip}}%
}
\def\logo{template/logo-black-white.png}
\definetrim{logotrim}{0 100px 0 100px}

% Define a copyright claimer.
\def\claimer{\color{black!40}All information in this document is the intellectual property of \doccopyright{}. You are not allowed to disclose any information herein to a third party prior to written consent from \doccopyright{}. All rights reserved. \copyright \doccopyright{}}

% Sets the counting depths for TOC
\setcounter{tocdepth}{4}
\setcounter{topnumber}{5}
\setcounter{totalnumber}{6}

% Change paragraph to act as a subsubsubsection
\setcounter{secnumdepth}{4}
\titleformat{\paragraph}[hang]{\normalfont\normalsize\bfseries}{\theparagraph}{1em}{}
\titlespacing*{\paragraph}{0pt}{3.25ex plus 1ex minus .2ex}{1em}

% Setup colors
\definecolor{grey}{rgb}{0.75,0.75,0.75}
\definecolor{orchid}{rgb}{0.8516,0.4375,0.8359}

% Set internal link color
\hypersetup{linkcolor=orchid}

% Setup how the TOC looks
% Section
\titlecontents*{section}[1.5em]
	{\scshape\bfseries}
	{\thecontentslabel\hspace*{1pc}}
	{}
	{\normalfont\titlerule*[1pc]{.}\contentspage\\[1mm]}
% Subsection
\titlecontents*{subsection}[2em]
	{\normalfont\scshape}
	{\thecontentslabel\hspace*{1pc}}
	{}
	{\titlerule*[1pc]{.}\contentspage\\[0.6mm]}
% Subsubsection
\titlecontents*{subsubsection}[2em]
	{\normalfont}
	{\thecontentslabel\hspace*{1pc}}
	{}
	{\titlerule*[1pc]{.}\contentspage\\[0.3mm]}
% Paragraph (subsubsubsection)
\titlecontents*{paragraph}[2em]
	{\normalfont}
	{\thecontentslabel\hspace*{1pc}\itshape}
	{}
	{\normalfont\titlerule*[1pc]{.}\contentspage\\[0.3mm]}

% Setup the listings package
\lstset{breaklines=true,basicstyle=\ttfamily,moredelim=[is][\bfseries]{€}{€}}

% Setup how the headings look
% Section
\renewcommand\section{\@startsection {section}{1}{\z@}%
                                   {-3.5ex \@plus -1ex \@minus -.2ex}%
                                   {2.3ex \@plus.2ex}%
                                  {\scshape\Large\bfseries}}
% Subsection
\renewcommand\subsection{\@startsection {subsection}{1}{\z@}%
                                   {-3.5ex \@plus -1ex \@minus -.2ex}%
                                   {2.3ex \@plus.2ex}%
                                  {\scshape\large\bfseries}}

% Setup how floats are placed on the pages
\renewcommand{\topfraction}{.95}
\renewcommand{\textfraction}{.05}
\renewcommand{\floatpagefraction}{.75}

% Setup the headers and footers
% Fancy style
\pagestyle{fancy}
\fancyhf{}% Clear all settings
\fancyhead[RE,RO]{\raisebox{0.5cm}{\textsf{\begin{tabular}{p{6.5cm}p{2.8cm}p{0.7cm}}
\textbf{\large\docname} & {\footnotesize Ref} &{\footnotesize By}\tabularnewline
\multirow{3}{7cm}[1ex]{\doccategory}&\textrm{\small\docref} & \textrm{\small\docby} \tabularnewline
&{\footnotesize Date} & {\footnotesize Issue}\tabularnewline
&\textrm{\small\today} & \textrm{\small\docissuemajor\docissueminor} \tabularnewline
\end{tabular}}}}
\fancyhead[LE,LO]{\hspace*{0.2cm}\includegraphics[logotrim, width=4.5cm]{\logo}}
\fancyfoot[RO]{%
	\thepage(\pageref*{LastPage})
	\begin{tikzpicture}[overlay,remember picture]
		\node [rotate=-90, font=\tiny, yshift=-0.6cm, text width=9cm] at (current page.east)
		 {\claimer
		};
	\end{tikzpicture}
	}
\fancyfoot[LE]{%
	\thepage(\pageref*{LastPage})
	\begin{tikzpicture}[overlay,remember picture]
		\node [rotate=90, font=\tiny, yshift=-0.6cm, text width=9cm] at (current page.west)
		 {\claimer
		};
	\end{tikzpicture}
	}
% Blankpage style
\fancypagestyle{blankpage}{ %
\fancyhf{}% Clear all settings
\renewcommand{\headrulewidth}{0pt} % remove lines as well
\renewcommand{\footrulewidth}{0pt}
\fancyfoot[RO]{%
	\thepage(\pageref*{LastPage})
	\begin{tikzpicture}[overlay,remember picture]
		\node [rotate=-90, font=\tiny, yshift=-0.6cm, text width=9cm] at (current page.east)
		 {\claimer
		};
	\end{tikzpicture}
	}
\fancyfoot[LE]{%
	\thepage(\pageref*{LastPage})
	\begin{tikzpicture}[overlay,remember picture]
		\node [rotate=90, font=\tiny, yshift=-0.6cm, text width=9cm] at (current page.west)
		 {\claimer
		};
	\end{tikzpicture}
	}
\vspace*{10cm}
\Huge{\color{grey}This page was intentionally left blank.}
\vspace*{\fill}
}

% ******************************************************
% Make it easy to use appendices
% ******************************************************
\newcommand{\app}{%
\appendix%
\clearpage{\thispagestyle{blankpage}\cleardoublepage}%
}

% ******************************************************
% Generate cover page/toc etc.
% ******************************************************

\renewcommand{\maketitle}{
	\pagestyle{empty}
	\thispagestyle{empty}
	%--- Make title page
	\setcounter{page}{1}
	\begin{center}
		\includegraphics[logotrim, width=6.5cm]{\logo}\\[1mm]
		\vspace{0.5cm} \mbox{}\hrulefill \mbox{}\\[1.5cm]
     		{\Huge \textbf{\textsc{\doctitle\\[2cm]}}}
     		{\LARGE \textbf{\docname}}\\[15mm]
     		{\large \doccategory} \vfill
     		{\large \mbox{}\hrulefill\mbox{}\\[50mm]}
  	\end{center}
	\clearpage{\thispagestyle{blankpage}\cleardoublepage}
	\pagestyle{fancy}
}
%--- Make TOC
\newcommand{\maketoc}{
	\pagestyle{fancy}
	\thispagestyle{fancy}
  \tableofcontents
	\clearpage{\thispagestyle{blankpage}\cleardoublepage}
	\pagestyle{fancy}
}


% ******************************************************
% Define a ToDo-command.
% ******************************************************
\newcommand{\todo}[1]{%
\noindent\textcolor{red}{\textbf{TODO:} #1}
}
