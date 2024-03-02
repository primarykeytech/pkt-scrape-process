import sys
import pktscrape.pktscrape


def main():
    """
    Main function to run depending on the argument.
    Valid arguments are:
         scrape - runs the scraping process.
    """
    # get the command line arguments.
    args = sys.argv[1:]

    print(args)

    if len(args) == 0:
        print("No arguments provided. Exiting.")
        sys.exit(0)
    elif len(args) > 0:
        if args[0] == "scrape":
            print("Running the scraping process...")
            pktscrape.scrape_experiences()


if __name__ == "__main__":
    main()
