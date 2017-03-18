# ale3andro's lab_organizr
## Περί
Το λογισμικό αυτό είναι ένα έργο που φιλοδοξεί να κάνει την ευκολότερη τη
δουλειά ενός Administrator ενός σχολικού εργαστηρίου Πληροφορικής που
τρέχει Linux.
Μια σειρά από διαχειριστικές εργασίες (αποστολή αρχείων, λήψη αρχείων,
κλείσιμο διεργασίας, επανεκκίνηση X Server κλπ) μπορούν να γίνουν με 2-3 κλικ
ώστε να μην χάνεται πολύτιμος χρόνος μέσα στην τάξη.
Επίσης γίνονται παράλληλα με χρήση πολλαπλών threads με αποτέλεσμα οι
παραπάνω εργασίες να γίνονται πολύ πολύ ταχύτερα

## Τι έχει γίνει (features)
* Κατηγορίες clients (client classes) ανάλογα με την διανομή Linux που τρέχουν
* Δυνατότητα επιλογής σύνδεσης ως desktop user ή user με δικαιώματα sudo
* Χρήση πολλαπλών threads ώστε να τελειώνουν οι εργασίας πολύ γρηγορότερα
* Ενσωμάτωση εργασιών σε μορφή modules γραμμένα σε json, δυνατότητα δημιουργίας custom Modules χωρίς αλλαγή κώδικα
* Υποστήριξη αποθήκευσης αρχείων (που λαμβάνονται από τους clients) σε online ή offline folder
* Δυνατότητα λήψης & αποστολής αρχείων στους clients με επιλογή τμήματος & ημερομηνίας
* Δυνατότητα εύκολης προσθήκης περισσότερων clients με προσθήκη των χαρακτηριστικών τους στο settings file
* Δυνατότητα λήψης αρχείων (όλων ή με συγκεκριμένες επεκτάσεις) από τις Επιφάνειες εργασίας των clients και αποθήκευση σε online ή offline φάκελο, σε υποφάκελο τμήματος και ημερομηνίας λήψης
* Δυνατότητα μαζικής επιστροφής αρχείων από αποθηκευμένο φάκελο στον server στους clients

## Τι δεν έχει γίνει ( & πρέπει να γίνει)
* ΣΟΒΑΡΟ! Όταν βάζεις περισσότερες από μια εντολές στη σειρά, εκτελούνται με ανάποδη σειρά!
* Δυνατότητα απομακρυσμένου ανοίγματος εφαρμογής στα πρότυπα του epoptes.org (export DISPLAY=:0)
* Προσθήκη δυνατότητας εμφάνισης των αρχείων των μαθητών που είναι αποθηκευμένα στην Επιφάνεια Εργασίας
* Να μπουν σε όλες τις "επικίνδυνες" εντολές try, except
* Ορισμένα actions να γίνουν built-in γιατί έτσι και αλλιώς δεν μπορεί να γίνει customization (όσα έχουν id=0)
* Τα scripts να μην δηλώνονται χειροκίνητα στο setting.json αλλά να διαβάζει η εφαρμογή αυτόματα όλα τα αρχεία τύπου json που είναι αποθηκευμένα σε συγκεκριμένο φάκελο (assets/scripts) και έχουνε
enabled=true

Τελευταία ενημέρωση: 2017-03-18
